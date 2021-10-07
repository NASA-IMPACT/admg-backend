from typing import Dict
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import aggregates
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import ListView, MultipleObjectMixin
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    FormView,
    FormMixin,
    ProcessFormView,
    ModelFormMixin,
)
from requests.api import get

from django_celery_results.models import TaskResult
import django_tables2
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django.shortcuts import render, redirect

from api_app.models import (
    ApprovalLog,
    Change,
    CREATE,
    UPDATE,
    CREATED_CODE,
    IN_REVIEW_CODE,
    IN_PROGRESS_CODE,
    AWAITING_REVIEW_CODE,
    IN_ADMIN_REVIEW_CODE,
    PUBLISHED_CODE,
    IN_TRASH_CODE,
    AVAILABLE_STATUSES,
)
from data_models import serializers


from .config import MODEL_CONFIG_MAP
from .published_forms import GenericFormClass
from .utils import compare_values
from .forms import TransitionForm


def GenericListView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericListViewClass(SingleTableMixin, FilterView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_list.html"
        table_class = MODEL_CONFIG_MAP[model_name]["table"]
        filterset_class = MODEL_CONFIG_MAP[model_name]["filter"]

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
                "model": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericListViewClass


class ModelObjectView(ModelFormMixin, DetailView):
    fields = "__all__"

    def _get_form(self, form, disable_all=False, **kwargs):
        form = form(**kwargs)
        if disable_all:
            for fieldname in form.fields:
                form.fields[fieldname].disabled = True

        return form

    def _get_form_model(self, model, disable_all=False, **kwargs):
        form = GenericFormClass(model=model)
        return self._get_form(form, disable_all, **kwargs)

    def _get_form_model_name(self, model_name, disable_all=False, **kwargs):
        form = GenericFormClass(model_name=model_name)
        return self._get_form(form, disable_all, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "object": self.get_object(),
            "request": self.request,
        }


def GenericDetailView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDetailViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = 'api_app/published_detail.html'

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_model_name(
                    model_name,
                    instance=kwargs.get('object'),
                    disable_all=True
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
            }

    return GenericDetailViewClass


def GenericEditView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericEditViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = 'api_app/published_edit.html'

        def post(self, request, **kwargs):
            model_instance = self.model.objects.get(uuid=kwargs.get('pk'))

            # do this here because the super().get_context_data looks for a self.object
            self.object = model_instance

            # getting form with instance and data gives a lot of changed fields
            # however, getting a form with initial and data only gives the required changed fields
            old_form = self._get_form_model_name(model_name, instance=model_instance)
            new_form = self._get_form_model_name(model_name, data=request.POST, initial=old_form.initial)

            kwargs = {**kwargs, 'object': model_instance}
            context = self.get_context_data(**kwargs)
            if new_form.is_valid():
                if len(new_form.changed_data) > 0:
                    diff_dict = {}
                    for changed_key in new_form.changed_data:
                        processed_value = Change._get_processed_value(
                            new_form[changed_key].value()
                        )
                        diff_dict[changed_key] = processed_value

                    model_to_query = MODEL_CONFIG_MAP[model_name]['model']
                    content_type = ContentType.objects.get_for_model(model_to_query)
                    change_object = Change.objects.create(
                        content_type=content_type,
                        status=CREATED_CODE,
                        action=UPDATE,
                        model_instance_uuid=kwargs.get("pk"),
                        update=diff_dict
                    )
                    change_object.save()
                    return redirect(reverse(
                        f"{MODEL_CONFIG_MAP[model_name]['singular_snake_case']}-list-draft"
                    ))

                context["message"] = "Nothing changed"
                return render(request, self.template_name, context)

            context["model_form"] = new_form
            return render(request, self.template_name, context)

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": self._get_form_model_name(model_name, instance=kwargs.get('object')),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericEditViewClass


@method_decorator(login_required, name="dispatch")
class DiffView(ModelObjectView):
    model = Change
    template_name = 'api_app/published_diff.html'

    def _compare_forms(self, updated_form, original_form, keys_to_compare):
        for key in keys_to_compare:
            if not compare_values(
                original_form[key].value(),
                updated_form[key].value()
            ):
                updated_form.add_classes(updated_form.fields[key], "changed-item")

    def initialize_forms(self, change_instance):
        model_instance = change_instance.content_object

        serializer_class = getattr(serializers, f"{change_instance.model_name}Serializer")
        serializer_obj = serializer_class(
            instance=model_instance,
            data=change_instance.update,
            partial=True
        )

        noneditable_published_form = self._get_form_model(
            MODEL_CONFIG_MAP[change_instance.model_name]["model"],
            disable_all=True,
            instance=model_instance,
            auto_id="readonly_%s"
        )

        if serializer_obj.is_valid():
            editable_form = self._get_form_model(MODEL_CONFIG_MAP[change_instance.model_name]["model"])
            editable_form.initial = {
                **noneditable_published_form.initial,
                **{key: serializer_obj.validated_data.get(key) for key in change_instance.update}
            }
            self._compare_forms(editable_form, noneditable_published_form, change_instance.update)
        else:
            raise Exception("Exception here")

        return editable_form, noneditable_published_form

    def post(self, request, **kwargs):
        change_instance = self.model.objects.get(uuid=kwargs.get('pk'))
        _, noneditable_published_form = self.initialize_forms(change_instance)

        updated_form = self._get_form_model(
            MODEL_CONFIG_MAP[change_instance.model_name]["model"],
            data=request.POST,
            initial=noneditable_published_form.initial
        )

        isvalid = updated_form.is_valid()

        # the super get_context_data wants an object
        self.object = change_instance
        context = {
            **super().get_context_data(**kwargs),
            "editable_update_form": updated_form,
            "noneditable_published_form": noneditable_published_form,
            "model_name": change_instance.model_name,
            "display_name": MODEL_CONFIG_MAP[change_instance.model_name]["display_name"],
        }
        if isvalid:
            diff_dict = {**change_instance.update}
            for changed_key in updated_form.changed_data:
                processed_value = Change._get_processed_value(updated_form[changed_key].value())
                diff_dict[changed_key] = processed_value

            self._compare_forms(updated_form, noneditable_published_form, updated_form.changed_data)

            change_instance.update = diff_dict
            change_instance.save()

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        change_instance = kwargs.get("object")
        editable_form, noneditable_published_form = self.initialize_forms(change_instance)

        return {
            **super().get_context_data(**kwargs),
            "editable_update_form": editable_form,
            "transition_form": TransitionForm(change=change_instance, user=self.request.user),
            "noneditable_published_form": noneditable_published_form,
            "model_name": change_instance.model_name,
            "display_name": MODEL_CONFIG_MAP[change_instance.model_name]["display_name"],
        }
