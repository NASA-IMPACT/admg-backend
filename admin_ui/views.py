from typing import Dict

import django_tables2
import requests
from api_app.models import (
    AVAILABLE_STATUSES,
    AWAITING_REVIEW_CODE,
    CREATE,
    CREATED_CODE,
    IN_ADMIN_REVIEW_CODE,
    IN_PROGRESS_CODE,
    IN_REVIEW_CODE,
    IN_TRASH_CODE,
    PUBLISHED_CODE,
    UPDATE,
    ApprovalLog,
    Change,
)
from cmr import tasks
from data_models.models import (
    DOI,
    IOP,
    Alias,
    Campaign,
    CampaignWebsite,
    CollectionPeriod,
    Deployment,
    Image,
    Instrument,
    PartnerOrg,
    Platform,
    PlatformType,
    SignificantEvent,
    Website,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import aggregates
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import (
    CreateView,
    FormMixin,
    FormView,
    ProcessFormView,
    UpdateView,
)
from django.views.generic.list import ListView, MultipleObjectMixin
from django_celery_results.models import TaskResult
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from admin_ui.config import MODEL_CONFIG_MAP

from . import filters, forms, mixins, tables


@login_required
@user_passes_test(lambda user: user.is_admg_admin())
def trigger_deploy(request):
    try:
        workflow = settings.GITHUB_WORKFLOW
    except AttributeError:
        messages.add_message(
            request,
            messages.ERROR,
            f"Failed to trigger deployment: Github workflow not specified in settings.",
        )
        return HttpResponseRedirect(reverse("summary"))

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
                f'<a href="https://github.com/{workflow["repo"]}/actions/workflows/{workflow["id"]}" target="_blank">here</a>.'
            ),
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Failed to trigger deployment: {response.text}"
        )

    return HttpResponseRedirect(reverse("summary"))


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
        return HttpResponseRedirect(reverse("doi-approval", args=[campaign.uuid]))


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
            .order_by("status", "update__concept_id")
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
                "uuid": v.uuid,
                "keep": (
                    False
                    if v.status == IN_TRASH_CODE
                    else (
                        None if v.status in [CREATED_CODE, IN_PROGRESS_CODE] else True
                    )
                ),
                "status": v.get_status_display(),
                "readonly": v.status == PUBLISHED_CODE,
                **v.update,
            }
            for v in paginated_queryset.only("uuid", "update", "status")
        ]

    def form_valid(self, formset):
        changed_dois = [
            form.cleaned_data for form in formset.forms if form.has_changed()
        ]

        to_update = []
        to_trash = []
        ignored_updates = []

        for doi in changed_dois:
            if doi["keep"] is False:
                to_trash.append(doi)
            else:
                to_update.append(doi)

        if to_trash:
            for doi in Change.objects.filter(
                uuid__in=[doi["uuid"] for doi in to_trash]
            ):
                doi.trash(user=self.request.user, doi=True)
                doi.save()

        if to_update:
            change_status_to_edit = []
            change_status_to_review = []
            stored_dois = Change.objects.in_bulk([doi["uuid"] for doi in to_update])
            for doi in to_update:
                stored_doi = stored_dois[doi["uuid"]]

                if stored_doi.status == PUBLISHED_CODE:
                    ignored_updates.append(doi)
                    continue

                # Persist DOI updates
                for field, value in doi.items():
                    if field in ["uuid", "keep"]:
                        continue
                    stored_doi.update[field] = value
                # never been previously edited and checkmark and trash haven't been selected
                if stored_doi.status == CREATED_CODE and doi["keep"] == None:
                    stored_doi.status = IN_PROGRESS_CODE
                    change_status_to_edit.append(stored_doi)
                # checkmark was selected
                elif doi["keep"] == True:
                    if stored_doi.status == IN_TRASH_CODE:
                        stored_doi.untrash(user=self.request.user, doi=True)
                    stored_doi.status = AWAITING_REVIEW_CODE
                    change_status_to_review.append(stored_doi)

            Change.objects.bulk_update(
                stored_dois.values(), ["update", "status"], batch_size=100
            )

            ApprovalLog.objects.bulk_create(
                [
                    ApprovalLog(
                        change=doi,
                        user=self.request.user,
                        action=ApprovalLog.EDIT,
                        notes="Transitioned via the DOI Approval form",
                    )
                    for doi in change_status_to_edit
                ]
            )

            ApprovalLog.objects.bulk_create(
                [
                    ApprovalLog(
                        change=doi,
                        user=self.request.user,
                        action=ApprovalLog.SUBMIT,
                        notes="Transitioned via the DOI Approval form",
                    )
                    for doi in change_status_to_review
                ]
            )

        messages.info(
            self.request,
            f"Updated {len(to_update) - len(ignored_updates)} and removed {len(to_trash)} DOIs.",
        )
        if ignored_updates:
            messages.warning(
                self.request,
                f"Ignored changes to published {len(ignored_updates)} DOIs.",
            )
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse("doi-approval", args=[self.kwargs["pk"]])


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
        url = reverse("change-update", args=[self.object.pk])
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
        url = reverse("change-update", args=[self.object.pk])
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
            "Platform": "platform-list-draft",
            "Instrument": "instrument-list-draft",
            "PartnerOrg": "partner_org-list-draft",
            "GcmdProject": "gcmd_project-list-draft",
            "GcmdInstrument": "gcmd_instrument-list-draft",
            "GcmdPlatform": "gcmd_platform-list-draft",
            "GcmdPhenomena": "gcmd_phenomena-list-draft",
            "FocusArea": "focus_area-list-draft",
            "GeophysicalConcept": "geophysical_concept-list-draft",
            "MeasurementRegion": "measurement_region-list-draft",
            "MeasurementStyle": "measurement_style-list-draft",
            "MeasurementType": "measurement_type-list-draft",
            "HomeBase": "home_base-list-draft",
            "PlatformType": "platform_type-list-draft",
            "GeographicalRegion": "geographical_region-season-list-draft",
            "Season": "season-season-list-draft",
            "WebsiteType": "website_type-list-draft",
            "Repository": "repository-list-draft",
        }
        return button_mapping.get(content_type, "summary")

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        return super().post(*args, **kwargs)


def generate_base_list_view(model_name):
    if MODEL_CONFIG_MAP[model_name]["admin_required_to_view"]:
        authorization_level = user_passes_test(lambda user: user.is_admg_admin())
    else:
        authorization_level = login_required

    @method_decorator(authorization_level, name="dispatch")
    class BaseListView(SingleTableMixin, FilterView):
        model = Change
        template_name = "api_app/change_list.html"
        filterset_class = MODEL_CONFIG_MAP[model_name]["draft_filter"]
        table_class = MODEL_CONFIG_MAP[model_name]["change_list_table"]
        linked_model = MODEL_CONFIG_MAP[model_name]["model"]

        def get_queryset(self):
            queryset = (
                Change.objects.of_type(self.linked_model)
                .add_updated_at()
                .order_by("-updated_at")
            )

            if self.linked_model == Platform:
                return queryset.annotate_from_relationship(
                    of_type=PlatformType,
                    uuid_from="platform_type",
                    to_attr="platform_type_name",
                )
            else:
                return queryset

        def get_context_data(self, **kwargs):
            return {
                **super().get_context_data(**kwargs),
                "url_name": MODEL_CONFIG_MAP[model_name]["singular_snake_case"],
                "model": self.linked_model._meta.model_name,
                "display_name": MODEL_CONFIG_MAP[model_name]["display_name"],
            }

    return BaseListView.as_view()


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
        return self.request.META.get("HTTP_REFERER") or super().get_success_url()
