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
from .utils import get_diff


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
                "display_name": model_name,
                "model": MODEL_CONFIG_MAP[model_name]["display_name"],
                "url_name": MODEL_CONFIG_MAP[model_name]["display_name"],
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
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericDetailViewClass


def GenericEditView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericEditViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = 'api_app/published_edit.html'

        def post(self, request, **kwargs):
            self.object = self.model.objects.get(uuid=kwargs.get('pk'))
            old_form = self._get_form_model_name(model_name, instance=self.object)
            new_form = self._get_form_model_name(model_name, data=request.POST, initial=old_form.initial)
            kwargs = {**kwargs, 'object': self.object}
            context = self.get_context_data(**kwargs)
            if new_form.is_valid():
                if len(new_form.changed_data) > 0:
                    diff_dict = {}
                    for changed_key in new_form.changed_data:
                        processed_value = Change._get_processed_value(new_form[changed_key].value())
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
                        f"{MODEL_CONFIG_MAP[model_name]['display_name']}-list"
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


def GenericDiffView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDiffViewClass(ModelObjectView):
        model = Change
        template_name = 'api_app/published_diff.html'

        def get_context_data(self, **kwargs):
            change_instance = kwargs.get('object')
            model_instance = change_instance.content_object

            serializer_class = getattr(serializers, f"{model_name}Serializer")
            serializer_obj = serializer_class(
                instance=model_instance,
                data=change_instance.update,
                partial=True
            )

            if serializer_obj.is_valid():
                editable_form = self._get_form_model(MODEL_CONFIG_MAP[model_name]["model"])
                editable_form.initial = {
                    **editable_form.initial,
                    **{key: serializer_obj.data.get(key) for key in change_instance.update}
                }
            else:
                raise Exception("Exception here")

            return {
                **super().get_context_data(**kwargs),
                "editable_update_form": editable_form,
                "noneditable_published_form": self._get_form_model(
                    MODEL_CONFIG_MAP[model_name]["model"],
                    disable_all=True,
                    instance=model_instance,
                    auto_id="readonly_%s"
                ),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericDiffViewClass
