from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from api_app.admin import utils
from .inlines import PendingChangeInline, InProgressChangeInline
from ..models import APPROVED, APPROVED_CODE, Change, UPDATE, CREATE


SUBMODEL_FIELDNAME_PREFIX = "submodel__"


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


class ChangeAdmin(admin.ModelAdmin):
    # TODO: Filter content_type to be only those of interest to the data team
    change_form_template = "admin/change_model_detail.html"
    list_display = ("model_name", "added_date", "action", "status", "user")
    list_filter = (
        "status",
        "action",
        ModelToBeChangedFilter,
        "user",
        "added_date",
        "appr_reject_date",
    )
    readonly_fields = (
        "user",  # TODO: Admins should be able to change user
        # "update",
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

    def has_change_permission(self, request, obj: Change = None):
        """ Only allow changing objects if you're the author or superuser """
        if obj:
            # Nobody can edit an approved object
            if obj.status == APPROVED_CODE:
                return False

        return True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("content_type", "user")

    def save_model(self, request, obj: Change, form, change):
        print(change, obj)
        if not change:
            obj.update = {}
            obj.user = request.user

        else:

            def rm_prefix(name: str) -> str:
                return name[len(SUBMODEL_FIELDNAME_PREFIX) :]

            # Retrieve update data from form
            obj.update = {
                rm_prefix(k): v
                for k, v in form.data.dict().items()
                # Find field that have been name with special prefix
                if k.startswith(SUBMODEL_FIELDNAME_PREFIX) and
                # Update data should only be data that is different than previous
                v != obj.previous.get(rm_prefix(k))
            }

            # Validate update
            ModelForm = utils.get_modelform_for_content_type(obj.content_type)
            update_form = ModelForm(data=obj.update)
            update_form.full_clean()

            print(update_form.errors)
            print(update_form.cleaned_data)
            # if (obj.action in [CREATE, UPDATE]) and (not update_form.is_valid()):
            #     # TODO: Learn how django admin validates
            #     raise ValidationError(_(), update_form.errors)
        try:
            super().save_model(request, obj, form, change)
        except form.instance.__class__.DoesNotExist as e:
            raise ValidationError(_("Destination object does not exist")) from e

    def add_view(self, request, form_url="", extra_context=None):
        self.message_user(
            request,
            'To create a new entry for a data type, first select the appropriate "content type" and press the "Save and continue editing" button.  The appropriate editing form will then become visible.',
            level=messages.INFO,
        )
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """
        Overridden change_view. This will build a form to represent the Change's
        target model, allowing users to edit data with standard Field inputs
        that match the target model's field types.
        """
        # Buildout custom form for destination model
        obj = self.get_object(request, object_id)
        ModelForm = utils.get_modelform_for_content_type(obj.content_type)

        # We want to ensure that all the input fields for the custom submodel
        # form are prefixed with a string. This was, we can later distinguish
        # between fields relating to the Change model and those that relate to
        # the content_object
        form = ModelForm(
            obj.update,
            # TODO: This may be the correct way to prefix the submodel form
            # prefix=SUBMODEL_FIELDNAME_PREFIX,
            # empty_permitted=False
        )

        readonly = not self.has_change_permission(request, obj)
        for field in form.fields.values():
            utils.prefix_field(field, SUBMODEL_FIELDNAME_PREFIX)
            field.widget.attrs["disabled"] = readonly
            field.widget.attrs["readonly"] = readonly

        admin_form = admin.helpers.AdminForm(
            form=form,
            fieldsets=[
                (
                    f"{form.instance.__class__.__name__} Form",
                    {"fields": list(form.base_fields)},
                )
            ],
            prepopulated_fields={},
            readonly_fields=(),
            model_admin=self,
        )

        # Provide custom admin form as extra context to view (custom template
        # should render this extra context as a form)
        extra_context = extra_context or {}
        extra_context["modelform"] = admin_form
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


admin.site.register(Change, ChangeAdmin)
