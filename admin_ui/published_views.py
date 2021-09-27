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
from django.forms import ModelForm

from django.views.generic.edit import (
    CreateView,
    UpdateView,
    FormView,
    FormMixin,
    ProcessFormView,
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

from . import published_tables, forms, mixins, filters
from .config import MODEL_CONFIG_MAP


def GenericListView(model_name):
    print("comes here", model_name)
    @method_decorator(login_required, name="dispatch")
    class GenericListViewClass(SingleTableMixin, FilterView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = "api_app/published_list.html"
        table_class = MODEL_CONFIG_MAP[model_name]["table"]
        filterset_class = MODEL_CONFIG_MAP[model_name]["filter"]

        def get_context_data(self, **kwargs):
            print("model name is ", MODEL_CONFIG_MAP[model_name]["model"]._meta.model_name)
            return {
                **super().get_context_data(**kwargs),
                "display_name": model_name,
                "model": MODEL_CONFIG_MAP[model_name]["display_name"],
            }
    return GenericListViewClass


def GenericFormClass(model_name):
    class MyFormClass(ModelForm):
        def get_form(self, form_class=None):
            form = super().get_form()
            for field in form.fields:
                # Set html attributes as needed for all fields
                form.fields[field].widget.attrs['readonly'] = 'readonly'          
                form.fields[field].widget.attrs['disabled'] = 'disabled'

            return form
        class Meta:
            model = MODEL_CONFIG_MAP[model_name]["model"]
            fields = '__all__'
        
    return MyFormClass


def GenericDetailView(model_name):
    @method_decorator(login_required, name="dispatch")
    class GenericDetailViewClass(DetailView):
        model = MODEL_CONFIG_MAP[model_name]["model"]
        template_name = 'api_app/published_detail.html'
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            print('#'*100, kwargs)
            context['model_form'] = GenericFormClass(model_name)(
                instance=kwargs.get('object')
            )
            return context
    return GenericDetailViewClass
