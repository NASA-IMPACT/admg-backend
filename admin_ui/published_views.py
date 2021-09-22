from typing import Dict

from django.conf import settings
from django.contrib import messages
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
from cmr import tasks
from data_models.models import (
    Alias,
    Campaign,
    CampaignWebsite,
    CollectionPeriod,
    Deployment,
    DOI,
    Image,
    Instrument,
    Platform,
    PlatformType,
    PartnerOrg,
    IOP,
    SignificantEvent,
    GcmdInstrument,
    GcmdProject,
    GcmdPhenomena,
    GcmdPlatform,
    FocusArea,
    GeophysicalConcept,
    MeasurementRegion,
    MeasurementStyle,
    MeasurementType,
    HomeBase,
    GeographicalRegion,
    Season,
    WebsiteType,
    Website,
    Repository,
)
from . import published_tables, forms, mixins, filters


@method_decorator(login_required, name="dispatch")
class CampaignListView(SingleTableMixin, FilterView):
    model = Campaign
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedCampaignListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Camapaign",
            "model": Campaign._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class PlatformListView(SingleTableMixin, FilterView):
    model = Platform
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedPlatformListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Platform",
            "model": Platform._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class InstrumentListView(SingleTableMixin, FilterView):
    model = Instrument
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedBasicListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Instrument",
            "model": Instrument._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class PartnerOrgListView(SingleTableMixin, FilterView):
    model = PartnerOrg
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedBasicListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Partner Organization",
            "model": PartnerOrg._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class WebsiteListView(SingleTableMixin, FilterView):
    model = Website
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedWebsiteListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Website",
            "model": Website._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class AliasListView(SingleTableMixin, FilterView):
    model = Alias
    template_name = "api_app/published_list.html"
    table_class = published_tables.PublishedAliasListTable
    filterset_class = filters.ChangeStatusFilter

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Alias",
            "model": Alias._meta.model_name,
        }


# TODO: Come back to this. Multi model views
# @method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldGCMDListView(View):
    pass

# @method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldScienceListView(View):
    pass


# @method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldMeasurmentPlatformListView(View):
    pass


# @method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldRegionSeasonListView(View):
    pass


# @method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldWebsiteListView(View):
    pass
