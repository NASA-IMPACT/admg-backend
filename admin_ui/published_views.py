from api_app.models import (
    CREATED_CODE,
    DELETE,
    IN_TRASH_CODE,
    PUBLISHED_CODE,
    UPDATE,
    Change,
)
from data_models import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .config import MODEL_CONFIG_MAP
from .forms import TransitionForm
from .published_forms import GenericFormClass
from .utils import compare_values
from .mixins import ChangeModelFormMixin


def GenericListView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericListViewClass(SingleTableMixin, FilterView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_list.html"
        table_class = MODEL_CONFIG_MAP[model_name]["published_table"]
        filterset_class = MODEL_CONFIG_MAP[model_name]["published_filter"]

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
                "model": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericListViewClass


class ModelObjectView(ChangeModelFormMixin, DetailView):
    fields = "__all__"

    @staticmethod
    def is_published_or_trashed(change_instance):
        return (
            change_instance.status == PUBLISHED_CODE
            or change_instance.status == IN_TRASH_CODE
        )

    def _initialize_form(self, form_class, disable_all=False, **kwargs):
        form_instance = form_class(**kwargs)

        # prevent fields from being edited
        if disable_all:
            for fieldname in form_instance.fields:
                form_instance.fields[fieldname].disabled = True

        return form_instance

    def _get_form_from_model_name(self, model_name, disable_all=False, **kwargs):
        form_class = GenericFormClass(model_name)
        return self._initialize_form(form_class, disable_all, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "object": self.get_object(),
            "request": self.request,
        }

    def _create_diff_dict(self, form):
        updated_values = self.get_update_values(form)
        return {
            changed_key: updated_values[changed_key]
            for changed_key in form.changed_data
        }


def GenericDetailView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDetailViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_detail.html"

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_from_model_name(
                    model_name, instance=kwargs.get("object"), disable_all=True
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericDetailViewClass


def GenericEditView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericEditViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_edit.html"

        def post(self, request, **kwargs):
            # do this here because the super().get_context_data looks for a self.object
            self.object = self.model.objects.get(uuid=kwargs.get("pk"))

            # getting form with instance and data gives a lot of changed fields
            # however, getting a form with initial and data only gives the required changed fields
            old_form = self._get_form_from_model_name(model_name, instance=self.object)
            new_form = self._get_form_from_model_name(
                model_name,
                data=request.POST,
                initial=old_form.initial,
                files=request.FILES,
            )

            kwargs = {**kwargs, "object": self.object}
            context = self.get_context_data(**kwargs)

            if not len(new_form.changed_data):
                context["message"] = "Nothing changed"
                return render(request, self.template_name, context)

            diff_dict = self._create_diff_dict(new_form)
            model_to_query = MODEL_CONFIG_MAP[model_name]["model"]
            content_type = ContentType.objects.get_for_model(model_to_query)
            change_object = Change.objects.create(
                content_type=content_type,
                status=CREATED_CODE,
                action=UPDATE,
                model_instance_uuid=kwargs.get("pk"),
                update=diff_dict,
            )
            return redirect(reverse("change-update", kwargs={"pk": change_object.uuid}))

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_from_model_name(
                    model_name, instance=kwargs.get("object")
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericEditViewClass


def GenericDeleteView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDeletelViewClass(View):
        def dispatch(self, *args, **kwargs):
            model_to_query = MODEL_CONFIG_MAP[model_name]["model"]
            content_type = ContentType.objects.get_for_model(model_to_query)
            change_object = Change.objects.create(
                content_type=content_type,
                status=CREATED_CODE,
                action=DELETE,
                model_instance_uuid=kwargs.get("pk"),
                update={},
            )
            change_object.save()
            return redirect(
                reverse(
                    f"{MODEL_CONFIG_MAP[model_name]['singular_snake_case']}-list-draft"
                )
            )

    return GenericDeletelViewClass
