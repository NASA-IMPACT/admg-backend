from urllib.parse import urlparse
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
    IN_REVIEW_CODE,
    IN_ADMIN_REVIEW_CODE,
    PUBLISHED_CODE,
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
from . import tables, forms, mixins, filters


@login_required
@user_passes_test(lambda user: user.is_admg_admin())
def trigger_deploy(request):
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

    return HttpResponseRedirect(reverse("mi-summary"))


@method_decorator(login_required, name="dispatch")
class SummaryView(django_tables2.SingleTableView):
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
class CampaignListView(SingleTableMixin, FilterView):
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
class CampaignDetailView(DetailView):
    model = Change
    template_name = "api_app/campaign_detail.html"
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
            .annotate_from_relationship(
                of_type=Platform, uuid_from="platform", to_attr="platform_name"
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
class DoiFetchView(View):
    queryset = Change.objects.of_type(Campaign)

    def get_object(self):
        try:
            return self.queryset.get(uuid=self.kwargs["pk"])
        except self.queryset.model.DoesNotExist as e:
            raise Http404("Campaign does not exist") from e

    def post(self, request, **kwargs):
        campaign = self.get_object()
        task = tasks.match_dois.delay(campaign.content_type.model, campaign.uuid)
        past_doi_fetches = request.session.get("doi_task_ids", {})
        uuid = str(self.kwargs["pk"])
        request.session["doi_task_ids"] = {
            **past_doi_fetches,
            uuid: [task.id, *past_doi_fetches.get(uuid, [])],
        }
        messages.add_message(
            request,
            messages.INFO,
            f"Fetching DOIs for {campaign.update.get('short_name', uuid)}...",
        )
        return HttpResponseRedirect(reverse("mi-doi-approval", args=[campaign.uuid]))


@method_decorator(login_required, name="dispatch")
class DoiApprovalView(SingleObjectMixin, MultipleObjectMixin, FormView):
    form_class = forms.DoiFormSet
    template_name = "api_app/campaign_dois.html"
    paginate_by = 10
    campaign_queryset = Change.objects.of_type(Campaign)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.campaign_queryset)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Change.objects.of_type(DOI).filter(
                update__campaigns__contains=str(self.kwargs["pk"])
            )
            # Order the DOIs by review status so that unreviewed DOIs are shown first
            .order_by("-update__keep", "-status", "update__concept_id")
        )

    def get_context_data(self, **kwargs):
        uuid = str(self.kwargs["pk"])
        all_past_doi_fetches = self.request.session.get("doi_task_ids", {})
        if not isinstance(all_past_doi_fetches, dict):
            all_past_doi_fetches = {}
        relevant_doi_fetches = all_past_doi_fetches.get(uuid, [])
        doi_tasks = {task_id: None for task_id in relevant_doi_fetches}
        if relevant_doi_fetches:
            doi_tasks.update(
                TaskResult.objects.in_bulk(relevant_doi_fetches, field_name="task_id")
            )
        return super().get_context_data(
            **{
                "object_list": self.get_queryset(),
                "form": None,
                "formset": self.get_form(),
                "doi_tasks": doi_tasks,
            }
        )


    def get_initial(self):
        # This is where we generate the DOI data to be shown in the formset
        queryset = self.get_queryset()
        page_size = self.get_paginate_by(queryset)
        _, _, paginated_queryset, _ = self.paginate_queryset(queryset, page_size)
        return [
            {
                "uuid": v["uuid"],
                # "keep": v["update"].get("keep"),
                "keep": False if v['status']==7 else (True if v['status'] not in [0,1] else None),
                **v["update"],
            }
            for v in paginated_queryset.values("uuid", "update", "status")
        ]

    def form_valid(self, formset):
        changed_dois = [
            form.cleaned_data for form in formset.forms if form.has_changed()
        ]

        to_update = []
        to_trash = []
        for doi in changed_dois:
            if doi["keep"] is False:
                to_trash.append(doi)
            else:
                to_update.append(doi)

        if to_trash:
            for doi in Change.objects.filter(
                uuid__in=[doi["uuid"] for doi in to_trash]
            ):
                doi.trash(user=self.request.user)
                # doi.update["keep"] = False
                doi.save()

        if to_update:
            change_status_to_edit = []
            change_status_to_review = []
            stored_dois = Change.objects.in_bulk([doi["uuid"] for doi in to_update])
            for doi in to_update:
                # Persist DOI updates
                for field, value in doi.items():
                    if field in ["uuid", "keep"]:
                        continue
                    stored_doi = stored_dois[doi["uuid"]]
                    stored_doi.update[field] = value
                # never been previously edited and checkmark and trash haven't been selected
                if stored_doi.status == 0 and doi['keep'] == None:
                    stored_doi.status = 1
                    change_status_to_edit.append(stored_doi)
                # checkmark was selected
                elif doi['keep'] == True:
                    if stored_doi.status == 7:
                        stored_doi.untrash(user=self.request.user)
                    stored_doi.status = 3
                    change_status_to_review.append(stored_doi)

            Change.objects.bulk_update(
                stored_dois.values(), ["update", "status"], batch_size=100
            )

            ApprovalLog.objects.bulk_create(
                [
                    ApprovalLog(
                        change=doi, user=self.request.user, action=ApprovalLog.EDIT
                    )
                    for doi in change_status_to_edit
                ]
            )

            ApprovalLog.objects.bulk_create(
                [
                    ApprovalLog(
                        change=doi, user=self.request.user, action=ApprovalLog.SUBMIT
                    )
                    for doi in change_status_to_review
                ]
            )

        messages.info(
            self.request, f"Updated {len(to_update)} and removed {len(to_trash)} DOIs."
        )
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse("mi-doi-approval", args=[self.kwargs["pk"]])


@method_decorator(login_required, name="dispatch")
class ChangeCreateView(mixins.ChangeModelFormMixin, CreateView):
    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/change_create.html"

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
            "content_type_name": (
                self.get_model_form_content_type().model_class().__name__
            ),
        }

    def get_success_url(self):
        url = reverse("mi-change-update", args=[self.object.pk])
        if self.request.GET.get("back"):
            return f'{url}?back={self.request.GET["back"]}'
        return url

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
    template_name = "api_app/change_update.html"
    queryset = (
        Change.objects.select_related("content_type")
        .prefetch_approvals()
        .annotate_from_relationship(
            of_type=Image, to_attr="logo_url", uuid_from="logo", identifier="image"
        )
    )

    def get_success_url(self):
        url = reverse("mi-change-update", args=[self.object.pk])
        if self.request.GET.get("back"):
            return f'{url}?back={self.request.GET["back"]}'
        return url

    def get_context_data(self, **kwargs):
        obj = self.get_object()
        return {
            **super().get_context_data(**kwargs),
            "transition_form": forms.TransitionForm(change=obj, user=self.request.user),
            "campaign_subitems": [
                "Deployment",
                "IOP",
                "SignificantEvent",
                "CollectionPeriod",
            ],
            "related_fields": self.get_related_fields(),
            "back_button": self.get_back_button_url(),
        }

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_related_fields(self) -> Dict:
        related_fields = {}
        content_type = self.get_model_form_content_type().model_class().__name__
        if content_type in [
            "Campaign",
            "Platform",
            "Deployment",
            "Instrument",
            "PartnerOrg",
        ]:
            related_fields["alias"] = Change.objects.of_type(Alias).filter(
                update__object_id=str(self.object.uuid)
            )
        if content_type == "Campaign":
            related_fields["campaignwebsite"] = (
                Change.objects.of_type(CampaignWebsite)
                .filter(action=CREATE, update__campaign=str(self.object.uuid))
                .annotate_from_relationship(
                    of_type=Website,
                    to_attr="title",
                    uuid_from="website",
                    identifier="title",
                )
            )
        return related_fields

    def get_model_form_intial(self):
        return self.object.update

    def get_back_button_url(self):
        """
        In the case where the back button returns the user to the table view for that model type, specify
        which table view the user should be redirected to.
        """
        content_type = self.get_model_form_content_type().model_class().__name__
        button_mapping = {
            "Platform": "mi-platform-list",
            "Instrument": "mi-instrument-list",
            "PartnerOrg": "mi-organization-list",
            "GcmdInstrument": "lf-gcmd-list",
            "GcmdPhenomena": "lf-gcmd-list",
            "GcmdPlatform": "lf-gcmd-list",
            "GcmdProject": "lf-gcmd-list",
            "FocusArea": "lf-science-list",
            "GeophysicalConcept": "lf-science-list",
            "MeasurementRegion": "lf-measure-platform-list",
            "MeasurementStyle": "lf-measure-platform-list",
            "MeasurementType": "lf-measure-platform-list",
            "HomeBase": "lf-measure-platform-list",
            "PlatformType": "lf-measure-platform-list",
            "GeographicalRegion": "lf-region-season-list",
            "Season": "lf-region-season-list",
            "WebsiteType": "lf-website-list",
            "Repository": "lf-website-list",
        }
        return button_mapping.get(content_type, "mi-summary")

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
            .annotate_from_relationship(
                of_type=PlatformType,
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


@method_decorator(login_required, name="dispatch")
class WebsiteListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.WebsiteChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return Change.objects.of_type(Website).filter(action=CREATE).add_updated_at()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Website",
            "model": Website._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class CampaignWebsiteListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.WebsiteChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return (
            Change.objects.of_type(CampaignWebsite)
            .filter(action=CREATE)
            .add_updated_at()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Campaign Website",
            "model": CampaignWebsite._meta.model_name,
        }


@method_decorator(login_required, name="dispatch")
class AliasListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    table_class = tables.AliasChangeListTable
    filterset_class = filters.ChangeStatusFilter

    def get_queryset(self):
        return Change.objects.of_type(Alias).filter(action=CREATE).add_updated_at()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Alias",
            "model": Alias._meta.model_name,
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


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class LimitedFieldWebsiteListView(SingleTableMixin, FilterView):
    model = Change
    item_types = [WebsiteType, Repository]

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
            "display_name": "Website Item",
            "is_multi_modelview": True,
            "item_types": [m._meta.model_name for m in self.item_types],
        }


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
