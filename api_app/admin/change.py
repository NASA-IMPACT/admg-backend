from django.forms import modelform_factory
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .inlines import PendingChangeInline, InProgressChangeInline
from ..models import Change, UPDATE, CREATE


class ChangableAdmin(admin.ModelAdmin):
    inlines = [PendingChangeInline, InProgressChangeInline]

    def save_model(self, request, obj, form, change):
        if request.user.is_superuser or not form.changed_data:
            return super().save_model(request, obj, form, change)
        # if action == CREATE:
        #     # the user should still be able to add in few partial fields
        #     serializer = self.get_serializer(data=request.data, partial=True)
        #     serializer.is_valid(raise_exception=True)
        # elif action == UPDATE:
        #     partial = action == PATCH or kwargs.pop('partial', False)
        #     instance = self.get_object()
        #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
        #     serializer.is_valid(raise_exception=True)

        # TODO:
        # serializer_class = getattr(sz, f"{self.model_name}Serializer")
        # instance = model.objects.get(uuid=self.model_instance_uuid)
        # if self.action == UPDATE:
        #     serializer = serializer_class(instance)

        return Change.objects.create(
            content_type=ContentType.objects.get_for_model(obj),
            update={k: form.data[k] for k in form.changed_data},
            model_instance_uuid=obj.uuid,
            action=UPDATE if change else CREATE,
            user=request.user,
        )


class ModelToBeChangedFilter(admin.SimpleListFilter):
    title = "data type"
    parameter_name = "content_type_id"

    def lookups(self, request, model_admin):
        return [
            (c.content_type_id, c.model_name)
            for c in Change.objects.distinct("content_type").select_related(
                "content_type"
            )
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(content_type_id=self.value())


class IsNewFilter(admin.SimpleListFilter):
    title = "is a new record"
    parameter_name = "is_new"

    def lookups(self, request, model_admin):
        return (("true", "True"), ("false", "False"))

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(previous={})
        elif self.value() == "false":
            return queryset.exclude(previous={})
        return queryset


class ChangeAdmin(admin.ModelAdmin):
    # TODO: Filter content_type to be only those of interest to the data team
    change_form_template = "admin/change_detail.html"
    list_display = ("model_name", "added_date", "status", "user", "is_new")
    list_filter = (
        "status",
        ModelToBeChangedFilter,
        "user",
        "added_date",
        "appr_reject_date",
        IsNewFilter,
    )
    readonly_fields = (
        "user",  # TODO: Admins should be able to change user
        "update",
        "previous",
        "uuid",
        "model_instance_uuid",
        "appr_reject_date",  # TODO: Admins should be able to change appr_reject_date
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "action",
                    "content_type",
                    # "added_date",
                )
            },
        ),
        (
            "Details",
            {"classes": (), "fields": ("user", "status", "appr_reject_date", "notes")},
        ),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": ("uuid", "model_instance_uuid", "previous", "update"),
            },
        ),
    )

    def is_new(self, obj):
        """ Information used in list_display to indicate if a record is new """
        return obj.previous == {}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content_type", "user")

    def _get_modelform_for_model(self, obj):
        """
        Returns a ModelForm for content object associated with a provided object.
        """
        Model = obj.content_type.model_class()
        return modelform_factory(Model, exclude=[])

    def _get_adminform_for_model(self, obj, field_name_prefix):
        """
        Helper to build form for Change's destination model.
        """
        ModelForm = self._get_modelform_for_model(obj)
        form = ModelForm(initial=obj.update)
        fieldsets = [
            (f"{form.instance.__class__.__name__} Form", {"fields": list(form.base_fields)})
        ]

        # We want to ensure that all the input fields for the model form are
        # prefixed with a string. This was, we can later distinguish between
        # fields relating to the Change model and those that relate to the
        # content_object
        for field in form.fields.values():
            # TODO: START HERE! SERIOUS! This seems to cause all widgets to use the same rederrer!
            old_render = field.widget.render

            def _widget_render_wrapper(name, *args, **kwargs):
                return old_render(f"{field_name_prefix}{name}", *args, **kwargs)

            field.widget.render = _widget_render_wrapper
        return admin.helpers.AdminForm(
            form,
            fieldsets,
            # Clear prepopulated fields on a view-only form to avoid a crash.
            # self.get_prepopulated_fields(request, obj)
            # if add or self.has_change_permission(request, obj)
            # else {},
            {},
            (),
            model_admin=self,
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
            obj.update = {}
        else:
            # Retrieve update data from form
            prefix = "subform__"
            obj.update = {
                k[len(prefix):]: v
                for k, v in form.data.dict().items()
                if k.startswith(prefix)
            }

            # Validate update
            ModelForm = self._get_modelform_for_model(obj)
            update_form = ModelForm(data=obj.update)
            if not update_form.is_valid():
                # TODO: Learn how django admin validates
                raise Exception("INVALID", update_form.errors)
        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        print(request.user)
        return {"action": CREATE, "user": request.user, "update": {}}

    # def add_view(self, request, form_url="", extra_context=None):
    #     form = super().add_view(request, form_url, extra_context)
    #     print(form)
    #     return form

    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     return self.changeform_view(request, object_id, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # https://github.com/django/django/blob/0004daa536890fdb389c895baaa21bea6a1f7073/django/contrib/auth/admin.py#L160-L161
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/contrib/admin/options.py#L1608-L1614
        extra_context = extra_context or {}
        extra_context["modelform"] = self._get_adminform_for_model(
            self.get_object(request, object_id), "subform__"
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


admin.site.register(Change, ChangeAdmin)
