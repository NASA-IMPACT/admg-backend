from typing import Dict

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

from django_celery_results.models import TaskResult
import django_tables2
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
import requests

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

from .config import MODEL_CONFIG_MAP
from .published_forms import GenericFormClass


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


def get_form_data(model_name, instance, disable_all=True):
    form = GenericFormClass(model_name)(instance=instance)
    if disable_all:
        for fieldname in form.fields:
            form.fields[fieldname].disabled = True
    
    return form


class ModelObjectView(ModelFormMixin, DetailView):
    fields = "__all__"
    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "object": kwargs.get('object'),
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
                "model_form": get_form_data(model_name, kwargs.get('object')),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericDetailViewClass


def GenericEditView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericEditViewClass(ModelObjectView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = 'api_app/published_edit.html'

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "model_form": get_form_data(model_name, kwargs.get('object'), False),
                "model_name": model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return GenericEditViewClass
