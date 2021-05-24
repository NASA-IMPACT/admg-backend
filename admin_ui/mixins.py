from functools import partial

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.fields import PolygonField
from django.db import models
from django.db.models import DateField
from django.forms import modelform_factory, FileField
from django.shortcuts import render
from django.views.generic.edit import ModelFormMixin

from . import fields, widgets


def formfield_callback(f, **kwargs):
    # Use ChangeChoiceField for any ForeignKey field in the model class
    if isinstance(f, models.ForeignKey):
        if f.remote_field.model != ContentType:
            kwargs.update(
                {
                    # Render link to open new window for creating new record
                    "widget": widgets.AddAnotherChoiceFieldWidget(
                        model=f.remote_field.model
                    ),
                    # Use field to handle drafts rather than published models
                    "form_class": partial(
                        fields.ChangeChoiceField, dest_model=f.remote_field.model
                    ),
                    # Choices consist of drafts rather than published models
                    "queryset": fields.ChangeChoiceField.get_queryset_for_model(
                        f.remote_field.model
                    ),
                }
            )
    elif isinstance(f, models.ImageField):
        kwargs.update(
            {
                "widget": widgets.ImagePreviewWidget,
            }
        )
    elif isinstance(f, PolygonField):
        kwargs.update(
            {
                "form_class": fields.BboxField,
            }
        )
    elif isinstance(f, DateField):
        kwargs.update(
            {
                "form_class": fields.CustomDateField,
            }
        )
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
        return modelform_factory(
            self.get_model_form_content_type().model_class(),
            exclude=[],
            formfield_callback=formfield_callback,
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
            data=request.POST, prefix=self.destination_model_prefix, files=request.FILES
        )
        model_form.full_clean()

        validate_model_form = "_validate" in request.POST
        if not form.is_valid() or (validate_model_form and not model_form.is_valid()):
            return self.form_invalid(form=form, model_form=model_form)

        # Populate Change's form with values from destination model's form.
        # We're not saving the cleaned_data because we want the raw text, not
        # the processed values (e.g. we don't want Polygon objects for bounding
        # boxes, rather we want the raw polygon text). This may or may not be
        # the best way to achieve this.
        form.instance.update = {
            name: field.widget.value_from_datadict(
                model_form.data, model_form.files, model_form.add_prefix(name)
            )
            for name, field in model_form.fields.items()
        }

        # Save any uploaded files to disk, then overwrite their values with their name
        for name, field in model_form.fields.items():
            if not isinstance(field, FileField):
                continue
            model_field = getattr(model_form.instance, name)
            if not model_field._file:
                continue
            model_field.save(model_field.url, model_form.cleaned_data[name])
            form.instance.update[name] = model_field.name

        return self.form_valid(form, model_form)

    def form_valid(self, form, model_form):

        # Important to run super first to set self.object
        redirect = super().form_valid(form)

        # If we're running validation...
        if "_validate" in self.request.POST:
            messages.success(self.request, f'Successfully validated "{self.object}".')
            return self.render_to_response(
                self.get_context_data(form=form, model_form=model_form)
            )

        # If form was submitted from a popup window...
        if "_popup" in self.request.GET:
            return render(
                self.request,
                template_name="snippets/close_popup_form.html",
                context={"object": self.object},
                status=201,
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
