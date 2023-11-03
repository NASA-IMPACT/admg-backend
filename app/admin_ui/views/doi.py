from typing import Sequence
from uuid import UUID
from api_app.views.generic_views import NotificationSidebar
from api_app.models import ApprovalLog, Change
from cmr import tasks
from data_models.models import DOI, Campaign
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from django.views.generic.list import MultipleObjectMixin
from django_celery_results.models import TaskResult

from .. import forms


def trash_dois(doi_uuids: Sequence[UUID], user: get_user_model()):
    for doi in Change.objects.filter(uuid__in=doi_uuids):
        doi.trash(user=user, doi=True)
        doi.save()


def update_dois(dois: Sequence[dict], user: get_user_model()):
    ignored_updates = []
    change_status_to_edit = []
    change_status_to_review = []
    stored_dois = Change.objects.in_bulk([doi["uuid"] for doi in dois])
    for doi in dois:
        stored_doi = stored_dois[doi["uuid"]]

        if stored_doi.status == Change.Statuses.PUBLISHED:
            ignored_updates.append(doi)
            continue

        # Persist DOI updates
        for field, value in doi.items():
            if field in ["uuid", "keep"]:
                continue
            stored_doi.update[field] = value
        # never been previously edited and checkmark and trash haven't been selected
        if stored_doi.status == Change.Statuses.CREATED and doi["keep"] is None:
            stored_doi.status = Change.Statuses.IN_PROGRESS
            stored_doi.updated_at = timezone.now()
            change_status_to_edit.append(stored_doi)
        # checkmark was selected
        elif doi["keep"] is True:
            if stored_doi.status == Change.Statuses.IN_TRASH:
                stored_doi.untrash(user=user, doi=True)
            stored_doi.status = Change.Statuses.AWAITING_REVIEW
            stored_doi.updated_at = timezone.now()
            change_status_to_review.append(stored_doi)

    Change.objects.bulk_update(
        stored_dois.values(), ["update", "updated_at", "status"], batch_size=100
    )

    ApprovalLog.objects.bulk_create(
        [
            ApprovalLog(
                change=doi,
                user=user,
                action=ApprovalLog.Actions.EDIT,
                notes="Transitioned via the DOI Approval form",
            )
            for doi in change_status_to_edit
        ]
    )

    ApprovalLog.objects.bulk_create(
        [
            ApprovalLog(
                change=doi,
                user=user,
                action=ApprovalLog.Actions.SUBMIT,
                notes="Transitioned via the DOI Approval form",
            )
            for doi in change_status_to_review
        ]
    )

    return change_status_to_edit + change_status_to_review, ignored_updates


@method_decorator(login_required, name="dispatch")
class DoiFetchView(NotificationSidebar, View):
    queryset = Change.objects.of_type(Campaign)

    def get_object(self):
        try:
            return self.queryset.get(uuid=self.kwargs["canonical_uuid"])
        except self.queryset.model.DoesNotExist as e:
            raise Http404("Campaign does not exist") from e

    def post(self, request, **kwargs):
        campaign = self.get_object()
        task = tasks.match_dois.delay(campaign.content_type.model, campaign.uuid)
        past_doi_fetches = request.session.get("doi_task_ids", {})
        uuid = str(self.kwargs["canonical_uuid"])
        request.session["doi_task_ids"] = {
            **past_doi_fetches,
            uuid: [task.id, *past_doi_fetches.get(uuid, [])],
        }
        messages.add_message(
            request,
            messages.INFO,
            f"Fetching DOIs for {campaign.update.get('short_name', uuid)}...",
        )
        return HttpResponseRedirect(reverse("doi-approval", args=[self.kwargs["canonical_uuid"]]))


@method_decorator(login_required, name="dispatch")
class DoiApprovalView(NotificationSidebar, SingleObjectMixin, MultipleObjectMixin, FormView):
    form_class = forms.DoiFormSet
    template_name = "api_app/campaign_dois.html"
    paginate_by = 10
    campaign_queryset = Change.objects.of_type(Campaign)
    pk_url_kwarg = "canonical_uuid"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.campaign_queryset)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Change.objects.of_type(DOI).filter(
                update__campaigns__contains=str(self.kwargs["canonical_uuid"])
            )
            # Order the DOIs by review status so that unreviewed DOIs are shown first
            .order_by("status", "update__concept_id")
        )

    def get_context_data(self, **kwargs):
        all_past_doi_fetches = self.request.session.get("doi_task_ids", {})
        if not isinstance(all_past_doi_fetches, dict):
            all_past_doi_fetches = {}
        relevant_doi_fetches = all_past_doi_fetches.get(self.kwargs["canonical_uuid"], [])
        doi_tasks = {task_id: None for task_id in relevant_doi_fetches}
        if relevant_doi_fetches:
            doi_tasks.update(TaskResult.objects.in_bulk(relevant_doi_fetches, field_name="task_id"))
        return super().get_context_data(
            **{
                # By setting the view model, our nav sidebar knows to highlight the link for campaigns
                'view_model': 'campaign',
                "canonical_uuid": self.kwargs["canonical_uuid"],
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
                    if v.status == Change.Statuses.IN_TRASH
                    else (
                        None
                        if v.status in [Change.Statuses.CREATED, Change.Statuses.IN_PROGRESS]
                        else True
                    )
                ),
                "status": v.get_status_display(),
                "readonly": v.status == Change.Statuses.PUBLISHED,
                **v.update,
            }
            for v in paginated_queryset.only("uuid", "update", "status")
        ]

    def form_valid(self, formset: forms.DoiFormSet):
        changed_dois: Sequence[forms.DoiForm] = [
            form.cleaned_data for form in formset.forms if form.has_changed()
        ]

        to_update: list[dict] = []
        to_trash: list[dict] = []

        for doi in changed_dois:
            if doi["keep"] is False:
                to_trash.append(doi)
            else:
                to_update.append(doi)

        if to_trash:
            trash_dois(doi_uuids=[doi["uuid"] for doi in to_trash], user=self.request.user)

        if to_update:
            updated_dois, ignored_dois = update_dois(dois=to_update)

        messages.info(
            self.request,
            f"Updated {len(updated_dois)} and removed {len(to_trash)} DOIs.",
        )

        if ignored_dois:
            messages.warning(
                self.request, f"Ignored changes to published {len(ignored_dois)} DOIs."
            )
        return super().form_valid(formset)

    def get_success_url(self):
        return reverse("doi-approval", args=[self.kwargs["canonical_uuid"]])
