import json

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Polygon
from django.db import models
from django.db.models.query import QuerySet
from django.forms import modelform_factory
from django.views.generic.edit import ModelFormMixin
from rest_framework.renderers import JSONRenderer


class ChangeModelFormMixin(ModelFormMixin):
    """
    This mixin attempts to simplify working with a second form (the model_form)
    when editing Change objects.
    """

    destination_model_prefix = "model_form"

    @property
    def destination_model_form(self):
        """ Helper to return a form for the destination of the Draft object """
        return modelform_factory(
            self.get_model_form_content_type().model_class(), exclude=[]
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

        if not form.is_valid():
            return self.form_invalid(form=form, model_form=model_form)

        # Populate Change's form with values from destination model's form
        form.instance.update = json.loads(
            JSONRenderer().render(
                {k: serialize(v) for k, v in model_form.cleaned_data.items()}
            )
        )
        return self.form_valid(form, model_form)

    def form_valid(self, form, model_form):
        # Save object
        messages.success(self.request, "Successfully updated form.")
        self.object = form.save()
        return self.render_to_response(
            self.get_context_data(form=form, model_form=model_form)
        )

    def form_invalid(self, form, model_form):
        # TODO: Can't save SignificantEvent instances
        # Overriden to support handling both invalid Change form and an invalid
        # destination model form
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
