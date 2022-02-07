from api_app.models import (
    AWAITING_REVIEW_CODE,
    CREATE,
    CREATED_CODE,
    IN_PROGRESS_CODE,
    IN_TRASH_CODE,
    PUBLISHED_CODE,
    UPDATE,
    ApprovalLog,
    Change,
)
from cmr import tasks
from data_models.models import DOI, Campaign
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import MultipleObjectMixin
from django_celery_results.models import TaskResult

from .. import forms, mixins


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
            Change.objects.of_type(DOI).filter(update__campaigns__contains=str(self.kwargs["pk"]))
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
            doi_tasks.update(TaskResult.objects.in_bulk(relevant_doi_fetches, field_name="task_id"))
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
                    else (None if v.status in [CREATED_CODE, IN_PROGRESS_CODE] else True)
                ),
                "status": v.get_status_display(),
                "readonly": v.status == PUBLISHED_CODE,
                **v.update,
            }
            for v in paginated_queryset.only("uuid", "update", "status")
        ]

    def form_valid(self, formset):
        changed_dois = [form.cleaned_data for form in formset.forms if form.has_changed()]

        to_update = []
        to_trash = []
        ignored_updates = []

        for doi in changed_dois:
            if doi["keep"] is False:
                to_trash.append(doi)
            else:
                to_update.append(doi)

        if to_trash:
            for doi in Change.objects.filter(uuid__in=[doi["uuid"] for doi in to_trash]):
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
                if stored_doi.status == CREATED_CODE and doi["keep"] is None:
                    stored_doi.status = IN_PROGRESS_CODE
                    change_status_to_edit.append(stored_doi)
                # checkmark was selected
                elif doi["keep"]:
                    if stored_doi.status == IN_TRASH_CODE:
                        stored_doi.untrash(user=self.request.user, doi=True)
                    stored_doi.status = AWAITING_REVIEW_CODE
                    change_status_to_review.append(stored_doi)

            Change.objects.bulk_update(stored_dois.values(), ["update", "status"], batch_size=100)

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
            "content_type_name": (self.get_model_form_content_type().model_class().__name__),
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