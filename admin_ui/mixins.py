import logging

from functools import partial
from typing import Dict, List

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.fields import PolygonField
from django.db import models as model_fields
from django.forms import modelform_factory, HiddenInput
from django.http import HttpResponseBadRequest
from django.http.response import Http404
from django.shortcuts import render
from django.views.generic.edit import ModelFormMixin
from api_app.urls import camel_to_snake

from data_models import models
from . import fields, widgets, config, utils

logger = logging.getLogger(__name__)


def log(description, model_form):
    logger.info('-' * 20 + description + '-' * 20)
    logger.info(
        f"model form metadata: {model_form.data.get('model_form-additional_metadata'),'empty'}"
    )
    logger.info(
        f"initial model form metadata: {model_form.data.get('initial-model_form-additional_metadata'),'empty'}"
    )
    logger.info(f"change-update: {model_form.data.get('change-update'),'empty'}")
    logger.info('-' * 60)


def formfield_callback(f, disabled_fields=[], **kwargs):
    """
    Custom logic for specifying widgets on a model form. To specify disabled_fields,
    developer must apply those via functools.partial before passing this function
    to a modelform factory.
    """
    # Use ChangeChoiceField for any ForeignKey field in the model class
    if isinstance(f, model_fields.ForeignKey):
        if f.remote_field.model == ContentType:
            kwargs.update({"widget": HiddenInput()})
        else:
            kwargs.update(
                {
                    # Render link to open new window for creating new record
                    "widget": widgets.AddAnotherChoiceFieldWidget(model=f.remote_field.model),
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

    if isinstance(f, model_fields.UUIDField):
        kwargs.update({"widget": HiddenInput()})
    elif isinstance(f, model_fields.ImageField):
        kwargs.update({"widget": widgets.ImagePreviewWidget})
    elif isinstance(f, PolygonField):
        kwargs.update({"form_class": fields.BboxField})
    elif isinstance(f, model_fields.DateTimeField):
        # DateTimeField is a subclass of DateTime, we don't want to use
        # CustomDateField widget
        pass
    elif isinstance(f, model_fields.DateField):
        kwargs.update({"form_class": fields.CustomDateField})
    elif isinstance(f, model_fields.BooleanField):
        # Adding choices assigns a "yes/no" option and creates a dropdown widget
        f.choices = ((True, "Yes"), (False, "No"))

    return f.formfield(disabled=f.name in disabled_fields, **kwargs)


class ChangeModelFormMixin(ModelFormMixin):
    """
    This mixin attempts to simplify working with a second form (the model_form)
    when editing Change objects.
    """

    destination_model_prefix = "model_form"

    @property
    def destination_model_form(self):
        """Helper to return a form for the destination of the Draft object"""
        model_type = self.get_model_type()

        # Disable any readonly fields
        model_name = camel_to_snake(model_type.__name__)
        model_config = config.MODEL_CONFIG_MAP.get(model_name, {})
        disabled_fields = model_config.get("change_view_readonly_fields", [])
        _formfield_callback = partial(formfield_callback, disabled_fields=disabled_fields)

        modelform = modelform_factory(
            model_type,
            exclude=[],
            formfield_callback=_formfield_callback,
            labels=self.get_verbose_names(model_type),
            help_texts=self.get_help_texts(model_type),
        )  # modelform generates a form class
        modelform.field_order = self.get_ordering(model_type)
        return modelform

    def get_model_type(self):
        # published items use self.model
        # However, we prioritize the self.get_model_form_content_type() function first
        try:
            model_type = self.get_model_form_content_type().model_class()
            if not model_type:
                raise Http404(f"Unsupported model type: {self.get_model_form_content_type()}")
        except NotImplementedError:
            if not self.model:
                raise NotImplementedError("Subclass must implement this property")
            model_type = self.model

        return model_type

    def get_model_form_content_type(self) -> ContentType:
        raise NotImplementedError("Subclass must implement this property")

    def get_model_form_intial(self):
        return {}

    def get_context_data(self, **kwargs):
        if "model_form" not in kwargs:
            # Ensure that the model_form is available in context for template
            kwargs["model_form"] = self.destination_model_form(
                initial=self.get_model_form_intial(), prefix=self.destination_model_prefix
            )

        # Disable save on published or trashed
        if self.object and self.object.is_locked:
            utils.disable_form_fields(kwargs['model_form'])

        return super().get_context_data(**kwargs)

    @staticmethod
    def get_verbose_names(model_type) -> Dict:
        return {
            "short_name": " ".join([model_type._meta.model_name.title(), "Short Name"]),
            "long_name": " ".join([model_type._meta.model_name.title(), "Long Name"]),
        }

    @staticmethod
    def get_help_texts(model_type) -> Dict[str, str]:
        if model_type == models.Campaign:
            return {
                "short_name": "Abbreviation for field investigation name (typically an acronym)",
                "long_name": "Full name of field investigation (typically the acronym fully spelled out)",
            }
        elif model_type == models.Deployment:
            return {
                "short_name": "Format as “dep_YYYY[i]” with YYYY as the year in which deployment begins, and optional lowercase character (i=a, b, …) appended only if there are multiple deployments in a single calendar year for the campaign",
                "long_name": "If there are named sub-campaigns, the name used for this deployment (e.g. CAMEX-3).  This may not exist.",
            }
        elif model_type == models.Platform:
            return {
                "short_name": "ADMG’s identifying name for the platform",
                "long_name": "ADMG’s full name for the platform",
            }
        elif model_type == models.Instrument:
            return {
                "short_name": "ADMG’s identifying name of the instrument (often an acronym)",
                "long_name": "Full name of the instrument",
            }
        elif model_type == models.SignificantEvent:
            return {
                "short_name": "ADMG's text identifier for the SE - format as 'XXX_SE_#' with XXX as the campaign shortname and # as the integer number of the SE within the campaign"
            }
        else:
            return {}

    @staticmethod
    def get_ordering(model_type) -> List[str]:
        if model_type == models.Deployment:
            return ["campaign"]
        if model_type in [models.IopSe, models.IOP]:
            return ["deployment"]
        if model_type == models.SignificantEvent:
            return [
                "deployment",
                "iop",
                "short_name",
                "start_date",
                "end_date",
                "description",
                "region_description",
                "published_list",
                "reports",
            ]
        if model_type == models.Platform:
            return ["short_name", "long_name", "platform_type"]
        else:
            return []

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        form.full_clean()

        logger.info('-' * 60 + 'initial data' + '-' * 60)
        logger.info(f"Printing request {request.POST}")
        logger.info(f"Printing get items {request.GET.items}")
        logger.info(f"clean form.data: {form.data}")
        logger.info('-' * 150)

        model_form = self.destination_model_form(
            data=request.POST, prefix=self.destination_model_prefix, files=request.FILES
        )
        model_form.full_clean()
        log("model_form after full clean", model_form)

        validate_model_form = "_validate" in request.POST
        if not form.is_valid() or (validate_model_form and not model_form.is_valid()):
            return self.form_invalid(form=form, model_form=model_form)

        if self.object and self.object.is_locked:
            return HttpResponseBadRequest("Object no longer available for edit")

        if form.instance._state.adding:
            # If we're create a new Change instance, we want to populate any fields that
            # are specified in the GET params. This is useful when we autopopulate a field
            # but that field is marked "disabled" (eg creating a Deployment draft with the
            # campaign field populated), this way we can retrieve the intended value of the
            # field even though its prepopulated field's values are not submitted with the
            # form.
            form.instance.update.update(
                {k: v for k, v in request.GET.items() if k in model_form.fields}
            )
        log("model_form before form.instance.update", model_form)
        data_to_update = {
            # Only update fields that can be altered by the form. Otherwise, retain
            # original values from form.instance.update
            k: v
            for k, v in utils.serialize_model_form(model_form).items()
            if not model_form.fields[k].disabled
        }
        form.instance.update.update(data_to_update)
        log("model_form after form.instance.update", model_form)

        return self.form_valid(form, model_form)

    def form_valid(self, form, model_form):
        # If we're running validation...
        if "_validate" in self.request.POST:
            messages.success(self.request, "Successfully validated.")
            return self.render_to_response(self.get_context_data(form=form, model_form=model_form))
        # Important to run super first to set self.object
        logger.info(f"Inside form_valid method --> form: {form.data}")
        logger.info(f"Inside form_valid method ---> model_form: {model_form.data}")
        redirect = super().form_valid(form)

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
            messages.error(self.request, f"Unable to save: {form.errors}")
        return self.render_to_response(self.get_context_data(form=form, model_form=model_form))


class DynamicModelMixin:
    """
    Helper model to retrieve model config based on model arg in URL
    """

    @property
    def _model_name(self):
        return self.kwargs['model']

    @property
    def _model_config(self):
        try:
            return config.MODEL_CONFIG_MAP[self._model_name]
        except KeyError:
            raise Http404(f"Bad model name: {self._model_name}")
