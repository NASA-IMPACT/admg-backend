from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.db.models import functions, expressions, aggregates, Max
from django.db.models.fields.json import KeyTextTransform
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import DetailView
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    View,
    FormMixin,
    ProcessFormView,
)
import django_tables2
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
import requests

from api_app.models import (
    ApprovalLog,
    Change,
    CREATE,
    UPDATE,
    IN_REVIEW_CODE,
    IN_ADMIN_REVIEW_CODE,
    PUBLISHED_CODE,
    AVAILABLE_STATUSES,
)
from data_models.models import (
    Campaign,
    CollectionPeriod,
    Deployment,
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
)
from . import tables, forms, mixins, filters


@login_required
@user_passes_test(lambda user: user.is_admg_admin())
def deploy_admin(request):
    workflow = settings.GITHUB_WORKFLOW

    response = requests.post(
        url=f"https://api.github.com/repos/{workflow['repo']}/actions/workflows/{workflow['id']}/dispatches",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {workflow['token']}",
        },
        json={"ref": workflow["branch"]},
    )
    if response.ok:
        messages.add_message(
            request,
            messages.INFO,
            mark_safe(
                "Successfully triggered deployment. See details "
                f'<a href="https://github.com/{workflow["repo"]}/actions?query=workflow%3ADeploy" target="_blank">here</a>.'
            ),
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Failed to trigger deployment: {response.text}"
        )

    # TODO: Redirect back to origin of request
    # TODO: Use dynamic admin route (either from URL router or from settings)
    return HttpResponseRedirect("/admin/")


@method_decorator(login_required, name="dispatch")
class ChangeSummaryView(django_tables2.SingleTableView):
    model = Change
    models = (Campaign, Platform, Instrument, PartnerOrg)
    table_class = tables.ChangeSummaryTable
    paginate_by = 10
    template_name = "api_app/summary.html"

    def get_queryset(self):
        return (
            Change.objects.of_type(*self.models)
            .filter(action=CREATE)
            # Prefetch related ContentType (used when displaying output model type)
            .select_related("content_type")
            .add_updated_at()
            .order_by("-updated_at")
        )

    def get_draft_status_count(self):
        status_ids = [IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE, PUBLISHED_CODE]
        status_translations = {
            status_id: status_name.replace(" ", "_")
            for status_id, status_name in AVAILABLE_STATUSES
        }

        # Setup dict with 0 counts
        review_counts = {
            model._meta.model_name: {
                status.replace(" ", "_"): 0 for status in status_translations.values()
            }
            for model in self.models
        }

        # Populate with actual counts
        model_status_counts = (
            Change.objects.of_type(*self.models)
            .filter(action=CREATE, status__in=status_ids)
            .values_list("content_type__model", "status")
            .annotate(aggregates.Count("content_type"))
        )
        for (model, status_id, count) in model_status_counts:
            review_counts.setdefault(model, {})[status_translations[status_id]] = count

        return review_counts

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            # These values for total_counts will be given to us by ADMG
            "total_counts": {"campaign": None, "platform": None, "instrument": None},
            "draft_status_counts": self.get_draft_status_count(),
            "activity_list": ApprovalLog.objects.prefetch_related(
                "change__content_type", "user"
            ).order_by("-date")[: self.paginate_by / 2],
        }


@method_decorator(login_required, name="dispatch")
class ChangeListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.CampaignChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return Change.objects.of_type(Campaign).filter(action=CREATE).add_updated_at()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Campaign",
            "model": "campaign",
        }


@method_decorator(login_required, name="dispatch")
class ChangeDetailView(DetailView):
    model = Change
    template_name = "api_app/change_detail.html"
    queryset = Change.objects.of_type(Campaign)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deployments = (
            Change.objects.of_type(Deployment)
            .filter(update__campaign=str(self.kwargs[self.pk_url_kwarg]))
            .prefetch_approvals()
            .order_by(self.get_ordering())
        )
        collection_periods = (
            Change.objects.of_type(CollectionPeriod)
            .filter(update__deployment__in=[str(d.uuid) for d in deployments])
            .select_related("content_type")
            .prefetch_approvals()
            .annotate_with_identifier_from_model(
                model=Platform, uuid_from="platform", to_attr="platform_name"
            )
        )

        # Build collection periods instruments (too difficult to do in SQL)
        instrument_uuids = set(
            uuid
            for instruments in collection_periods.values_list(
                "update__instruments", flat=True
            )
            for uuid in instruments
        )
        instrument_names = {
            str(uuid): short_name
            for uuid, short_name in Change.objects.of_type(Instrument)
            .filter(uuid__in=instrument_uuids)
            .values_list("uuid", "update__short_name")
        }
        for cp in collection_periods:
            cp.instrument_names = sorted(
                instrument_names.get(uuid) for uuid in cp.update.get("instruments")
            )

        return {
            **context,
            "deployments": deployments,
            "transition_form": forms.TransitionForm(
                change=context["object"], user=self.request.user
            ),
            "significant_events": (
                Change.objects.of_type(SignificantEvent)
                .filter(update__deployment__in=[str(d.uuid) for d in deployments])
                .select_related("content_type")
                .prefetch_approvals()
            ),
            "iops": (
                Change.objects.of_type(IOP)
                .filter(update__deployment__in=[str(d.uuid) for d in deployments])
                .select_related("content_type")
                .prefetch_approvals()
            ),
            "collection_periods": collection_periods,
        }

    def get_ordering(self):
        return self.request.GET.get("ordering", "-status")


@method_decorator(login_required, name="dispatch")
class ChangeCreateView(mixins.ChangeModelFormMixin, CreateView):
    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/change_add_form.html"

    def get_initial(self):
        # Get initial form values from URL
        return {
            "content_type": self.get_model_form_content_type(),
            "action": UPDATE if self.request.GET.get("uuid") else CREATE,
            "model_instance_uuid": self.request.GET.get("uuid"),
        }

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "content_type_name": self.get_model_form_content_type()
            .model_class()
            .__name__,
        }

    def get_success_url(self):
        return reverse("change-form", args=[self.object.pk])

    def get_model_form_content_type(self) -> ContentType:
        if not hasattr(self, "model_form_content_type"):
            self.model_form_content_type = ContentType.objects.get(
                app_label="data_models", model__iexact=self.kwargs["model"]
            )
        return self.model_form_content_type

    def get_model_form_intial(self):
        # TODO: Not currently possible to handle reverse relationships such as adding
        # models to a CollectionPeriod where the FK is on the Collection Period
        return {k: v for k, v in self.request.GET.dict().items() if k != "uuid"}

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = None
        return super().post(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ChangeUpdateView(mixins.ChangeModelFormMixin, UpdateView):
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/change_form.html"

    def get_success_url(self):
        return reverse("change-form", args=[self.object.pk])

    def get_queryset(self):
        # Prefetch content type for performance
        return Change.objects.select_related("content_type").prefetch_approvals()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "transition_form": forms.TransitionForm(
                change=self.get_object(), user=self.request.user
            ),
        }

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_model_form_intial(self):
        return self.object.update

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        return super().post(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class PlatformListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.PlatformChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return (
            Change.objects.of_type(Platform)
            .filter(action=CREATE)
            .add_updated_at()
            .annotate_with_identifier_from_model(
                model=PlatformType,
                uuid_from="platform_type",
                to_attr="platform_type_name",
            )
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Platform",
            "model": Platform._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class InstrumentListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.BasicChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return Change.objects.of_type(Instrument).filter(action=CREATE).add_updated_at()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Instrument",
            "model": Instrument._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class PartnerOrgListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.BasicChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return Change.objects.of_type(PartnerOrg).filter(action=CREATE).add_updated_at()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Partner Organization",
            "model": PartnerOrg._meta.model_name,
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldGCMDListView(SingleTableMixin, FilterView):
    model = Change
    item_types = [GcmdInstrument, GcmdPhenomena, GcmdPlatform, GcmdProject]

    template_name = "api_app/change_list.html"
    table_class = tables.MultiItemListTable
    filterset_class = filters.MultiItemFilter

    def get_queryset(self):

        return (
            Change.objects.of_type(*self.item_types)
            .filter(action=CREATE)
            .add_updated_at()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "GCMD Item",
            "is_multi_modelview": True,
            "item_types": [m._meta.model_name for m in self.item_types],
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldScienceListView(SingleTableMixin, FilterView):
    model = Change
    item_types = [FocusArea, GeophysicalConcept]

    template_name = "api_app/change_list.html"
    table_class = tables.MultiItemListTable
    filterset_class = filters.MultiItemFilter

    def get_queryset(self):

        return (
            Change.objects.of_type(*self.item_types)
            .filter(action=CREATE)
            .add_updated_at()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Science Concept",
            "is_multi_modelview": True,
            "item_types": [m._meta.model_name for m in self.item_types],
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldMeasurmentPlatformListView(SingleTableMixin, FilterView):
    model = Change
    item_types = [
        MeasurementRegion,
        MeasurementStyle,
        MeasurementType,
        HomeBase,
        PlatformType,
    ]

    template_name = "api_app/change_list.html"
    table_class = tables.MultiItemListTable
    filterset_class = filters.MultiItemFilter

    def get_queryset(self):

        return (
            Change.objects.of_type(*self.item_types)
            .filter(action=CREATE)
            .add_updated_at()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Measurement & Platform Item",
            "is_multi_modelview": True,
            "item_types": [m._meta.model_name for m in self.item_types],
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldRegionSeasonListView(SingleTableMixin, FilterView):
    model = Change
    item_types = [GeographicalRegion, Season]

    template_name = "api_app/change_list.html"
    table_class = tables.MultiItemListTable
    filterset_class = filters.MultiItemFilter

    def get_queryset(self):

        return (
            Change.objects.of_type(*self.item_types)
            .filter(action=CREATE)
            .add_updated_at()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Geographical Region & Season Item",
            "is_multi_modelview": True,
            "item_types": [m._meta.model_name for m in self.item_types],
        }


# “Website Types”: Website types, repository


@login_required
def to_be_developed(request):
    return render(request, "api_app/to_be_developed.html")


@method_decorator(login_required, name="dispatch")
class ChangeTransition(FormMixin, ProcessFormView, DetailView):
    model = Change
    form_class = forms.TransitionForm

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "change": self.get_object(),
            "user": self.request.user,
        }

    def form_valid(self, form):
        response = form.apply_transition()

        if response["success"]:
            obj = self.get_object()
            messages.success(
                self.request,
                (
                    f"Transitioned \"{obj.model_name}: {obj.update.get('short_name', obj.uuid)}\" "
                    f'to "{obj.get_status_display()}".'
                ),
            )
        else:
            messages.error(self.request, response["message"])

        return super().form_valid(form)

    def get_success_url(self):
        # TODO: Where should we direct to after approving a model?
        return urlparse(self.request.META.get("HTTP_REFERER")).path
