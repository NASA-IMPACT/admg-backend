import json
from functools import partial

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Polygon
from django.db import models
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet
from django.forms import modelform_factory
from django.views.generic.edit import ModelFormMixin
from rest_framework.renderers import JSONRenderer
from django.contrib.gis.admin import widgets as admin_widgets
from django.contrib.gis.db.models.fields import PolygonField

from api_app.models import Change
from .fields import ChangeChoiceField, BboxField
from .widgets import BoundingBoxWidget


def formfield_callback(f, **kwargs):
    # Use ChangeChoiceField for any ForeignKey field in the model class
    if isinstance(f, ForeignKey):
        kwargs = {
            **kwargs,
            "form_class": partial(ChangeChoiceField, dest_model=f.remote_field.model),
            "queryset": ChangeChoiceField.get_queryset_for_model(f.remote_field.model),
        }
    # if f.name == "spatial_bounds":
    #     print(f)
    # if isinstance(f, PolygonField):
    #     kwargs = {
    #         **kwargs,
    #         "form_class": BboxField,
    #         # "queryset": ChangeChoiceField.get_queryset_for_model(f.remote_field.model),
    #     }
    return f.formfield(**kwargs)


class ChangeModelFormMixin(ModelFormMixin):
    """
    This mixin attempts to simplify working with a second form (the model_form)
    when editing Change objects.
    """

    destination_model_prefix = "model_form"

    @property
    def destination_model_form(self):
        """ Helper to return a form for the destination of the Draft object """

        widgets = {}

        model_class = self.get_model_form_content_type().model_class()
        if model_class.__name__ == "Campaign":
            widgets["spatial_bounds"] = BoundingBoxWidget

        return modelform_factory(
            self.get_model_form_content_type().model_class(),
            exclude=[],
            formfield_callback=formfield_callback,
            widgets=widgets,
        )

    def get_model_form_content_type(self) -> ContentType:
        raise NotImplementedError("Subclass must implement this property")

    def get_model_form_intial(self):
        return {}

    def get_context_data(self, **kwargs):
        if "model_form" not in kwargs:
            # Ensure that the model_form is available in context for template
            kwargs["model_form"] = self.destination_model_form(
                initial=self.get_model_form_intial(),
                prefix=self.destination_model_prefix,
            )
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        form.full_clean()

        model_form = self.destination_model_form(
            data=request.POST, prefix=self.destination_model_prefix
        )
        model_form.full_clean()

        validate_model_form = "_validate" in request.POST
        if not form.is_valid() or (validate_model_form and not model_form.is_valid()):
            return self.form_invalid(form=form, model_form=model_form)

        # Populate Change's form with values from destination model's form
        form.instance.update = {
            name: field.widget.value_from_datadict(
                model_form.data, model_form.files, model_form.add_prefix(name)
            )
            for name, field in model_form.fields.items()
        }
        return self.form_valid(form, model_form)

    def form_valid(self, form, model_form):
        # Important to run super first to set self.object
        redirect = super().form_valid(form)

        if "_validate" in self.request.POST:
            messages.success(self.request, f'Successfully validated "{self.object}".')
            return self.render_to_response(
                self.get_context_data(form=form, model_form=model_form)
            )

        messages.success(self.request, 'Successfully saved "%s".' % self.object)
        return redirect

    def form_invalid(self, form, model_form):
        # TODO: Can't save SignificantEvent instances
        # Overriden to support handling both invalid Change form and an invalid
        # destination model form
        if not form.is_valid():
            messages.error(self.request, "Unable to save.")
        return self.render_to_response(
            self.get_context_data(form=form, model_form=model_form)
        )


def serialize(value):
    if isinstance(value, QuerySet):
        return [v.uuid for v in value]
    if isinstance(value, models.Model):
        return value.uuid
    if isinstance(value, Polygon):
        return value.wkt
    return value
