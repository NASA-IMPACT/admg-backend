from django.forms import modelform_factory
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType

from ..models import Change, UPDATE, CREATE, PATCH, PENDING_CODE, IN_PROGRESS_CODE


class BaseChangeInline(GenericTabularInline):
    model = Change
    ct_fk_field = "model_instance_uuid"

    extra = 0

    def has_add_permission(self, request, obj):
        # Changes may not be manually added. They should on be created by saving
        # a model
        return False

    def has_change_permission(self, request, obj):
        # Changes may not be manually added. They should on be created by saving
        # a model
        return False

    # TODO: Only let author or superuser change
    # https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin.has_change_permission
    # https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#inlinemodeladmin-options
    # Is it possible to determine change permissions on a per inline basis?


class PendingChangeInline(BaseChangeInline):
    verbose_name_plural = "Pending Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=PENDING_CODE)


class InProgressChangeInline(BaseChangeInline):
    verbose_name_plural = "In Progress Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=IN_PROGRESS_CODE)


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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content_type", "user")

    def is_new(self, obj):
        """ Information used in list_display to indicate if a record is new """
        return obj.previous == {}

    def get_change_update_form(self, obj):
        Model = obj.content_type.model_class()
        ModelForm = modelform_factory(Model, exclude=[])
        form = ModelForm(initial=obj.update)  # TODO: DOES NOT WORK
        # form = ModelForm()
        fieldsets = [(None, {"fields": list(form.base_fields)})]
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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # https://github.com/django/django/blob/0004daa536890fdb389c895baaa21bea6a1f7073/django/contrib/auth/admin.py#L160-L161
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/contrib/admin/options.py#L1608-L1614
        extra_context = extra_context or {}
        extra_context["modelform"] = self.get_change_update_form(
            self.get_object(request, object_id)
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


admin.site.register(Change, ChangeAdmin)
