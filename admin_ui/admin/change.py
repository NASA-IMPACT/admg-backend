from functools import partial
import json

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.forms import modelform_factory, Field
from django.forms.models import ModelForm as ModelFormType

from api_app.models import PUBLISHED_CODE, Change, CREATE
from .permissions import EnforcedPermissionsMixin


class ModelToBeChangedFilter(admin.SimpleListFilter):
    title = "data type"
    parameter_name = "content_type_id"

    def lookups(self, request, model_admin):
        return [("all", "Show all")] + [
            (c.content_type_id, c.model_name)
            for c in Change.objects.distinct("content_type").select_related("content_type")
        ]

    def queryset(self, request, queryset):
        content_type_id = self.value()
        return queryset.filter(content_type_id=content_type_id) if content_type_id else queryset


class ChangeAdmin(admin.ModelAdmin, EnforcedPermissionsMixin):
    SUBMODEL_FIELDNAME_PREFIX = "submodel__"

    change_form_template = "admin/change_model_detail.html"
    list_display = ("model_name", "action", "status")
    list_filter = ("status", "action", ModelToBeChangedFilter)
    readonly_fields = ("previous", "uuid", "model_instance_uuid")
    fieldsets = (
        (None, {"fields": ("action", "content_type")}),
        ("Details", {"classes": (), "fields": ("status",)}),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": ("uuid", "model_instance_uuid", "previous", "update"),
            },
        ),
    )

    def has_change_permission(self, request, obj: Change = None):
        """Only allow changing objects if you're the author or superuser"""
        if obj:
            # Nobody can edit a published object
            if obj.status == PUBLISHED_CODE:
                return False

        return True

    def has_add_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            # fetch related data to avoid followup lookups of needed data
            .select_related("content_type")
        )

    def get_changeform_initial_data(self, request):
        return {"action": CREATE}

    def save_model(self, request, obj: Change, form, change: bool):
        """
        Given a model instance save it to the database. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        # Retrieve update data from form
        model_fields = [
            (k[len(self.SUBMODEL_FIELDNAME_PREFIX) :], v)  # Rm prefix
            for k, v in form.data.dict().items()
            # Find field that have been name with special prefix
            if k.startswith(self.SUBMODEL_FIELDNAME_PREFIX)
        ]
        obj.update = {
            k: v
            for k, v in model_fields
            # Update data should only be data that is different than previous
            if v != obj.previous.get(k, "")
        }

        # Validate update
        ModelForm = self._get_modelform_for_model_class(request, obj.content_type.model_class())
        update_form = ModelForm(data=obj.update)
        update_form.full_clean()

        try:
            obj.save(post_save=True)  # Use post_save to opt-out of setting obj.previous
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
        obj = self.get_object(request, object_id)

        # Buildout custom form for destination model
        ModelCls = obj.content_type.model_class()
        ModelForm = self._get_modelform_for_model_class(request, ModelCls)
        model_form = ModelForm(
            {
                # some field widgets crash if passed None values
                **{f.name: "" for f in ModelCls._meta.fields},
                **(obj.previous or {}),
                **(obj.update or {}),
            }
        )

        # Ensure that JSONFields get data in form of raw text, not Python objects
        for field_name, field in model_form.fields.items():
            if field.__class__.__name__ == "JSONField":
                try:
                    json.loads(model_form.data[field_name])
                except TypeError:
                    model_form.data[field_name] = json.dumps(model_form.data[field_name])

        readonly = not self.has_change_permission(request, obj)
        if readonly:
            self.message_user(
                request,
                "You cannot edit Drafts after they have been published.",
                level=messages.WARNING,
            )

        for model_field in model_form.fields.values():
            # We want to ensure that all the input fields for the custom submodel
            # form are prefixed with a string. This way, we can later distinguish
            # between fields relating to the Change model and those that relate to
            # the content_object
            self._prefix_field(model_field, self.SUBMODEL_FIELDNAME_PREFIX)

            # Enforce admin state on model form
            model_field.widget.attrs["disabled"] = readonly
            model_field.widget.attrs["readonly"] = readonly

        admin_form = admin.helpers.AdminForm(
            form=model_form,
            fieldsets=[
                (
                    f"{model_form.instance.__class__.__name__} Form",
                    {"fields": list(model_form.base_fields)},
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
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def _get_modelform_for_model_class(self, request, ModelCls, **kwargs) -> ModelFormType:
        """
        Returns a ModelForm for provided model.
        """
        # Source: https://github.com/django/django/blob/e0a46367df8b17905f1c78f5c86f88d21c0f2b4d/django/contrib/admin/options.py#L698-L710
        return modelform_factory(
            ModelCls,
            **{
                "exclude": [],
                "formfield_callback": partial(self.formfield_for_dbfield, request=request),
                **kwargs,
            },
        )

    @staticmethod
    def _prefix_field(field: Field, field_name_prefix: str) -> None:
        """
        Mutate a provided field so that its rendered inputs have a name prefixed
        with the provided field name prefix.
        """
        renderer = field.widget.render

        def _widget_render_wrapper(name, *args, **kwargs):
            return renderer(f"{field_name_prefix}{name}", *args, **kwargs)

        field.widget.render = _widget_render_wrapper


admin.site.register(Change, ChangeAdmin)
