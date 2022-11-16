import logging
from typing import Dict

import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, OuterRef, Q, Value, aggregates, functions
from django.db.models.fields.json import KeyTextTransform
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormMixin, ProcessFormView, UpdateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from rest_framework.serializers import ValidationError

from admin_ui.config import MODEL_CONFIG_MAP
from api_app.models import ApprovalLog, Change, Recommendation, SubqueryCount
from api_app.urls import camel_to_snake
from api_app.views.generic_views import NotificationSidebar
from data_models.models import (
    IOP,
    Alias,
    Campaign,
    CollectionPeriod,
    Deployment,
    GcmdInstrument,
    GcmdPhenomenon,
    GcmdPlatform,
    GcmdProject,
    Image,
    Instrument,
    PartnerOrg,
    Platform,
    PlatformType,
    SignificantEvent,
    Website,
)
from kms import gcmd

from .. import filters, forms, mixins, tables, utils

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class SummaryView(NotificationSidebar, django_tables2.SingleTableView):
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

    def get_total_counts(self):
        return {
            model.__name__.lower(): Change.objects.of_type(model)
            .filter(action=Change.Actions.CREATE)
            .count()
            for model in self.models
        }

    def get_draft_status_count(self):
        statuses_count_create = [Change.Statuses.PUBLISHED]
        statuses_count_create_or_update = [
            Change.Statuses.IN_PROGRESS,
            Change.Statuses.IN_REVIEW,
            Change.Statuses.IN_ADMIN_REVIEW,
        ]

        status_translations = {k: v.replace(" ", "_") for k, v in Change.Statuses.choices}

        # Setup dict with 0 counts
        review_counts = {
            model._meta.model_name: {
                status.replace(" ", "_"): 0 for status in Change.Statuses.labels
            }
            for model in self.models
        }

        # Populate with actual counts
        model_status_counts = (
            Change.objects.of_type(*self.models)
            .filter(
                Q(action=Change.Actions.CREATE, status__in=statuses_count_create)
                | Q(
                    action__in=[Change.Actions.CREATE, Change.Actions.UPDATE],
                    status__in=statuses_count_create_or_update,
                )
            )
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
            "total_counts": self.get_total_counts(),
            "draft_status_counts": self.get_draft_status_count(),
            "activity_list": ApprovalLog.objects.prefetch_related(
                "change__content_type", "user"
            ).order_by("-date")[: self.paginate_by / 2],
        }


class CampaignDetailView(NotificationSidebar, DetailView):
    model = Change
    template_name = "api_app/campaign_details.html"
    queryset = Change.objects.of_type(Campaign)

    @staticmethod
    def _filter_latest_changes(change_queryset):
        """Returns the single latest Change draft for each model_instance_uuid in the
        provided queryset."""
        return change_queryset.order_by('model_instance_uuid', '-approvallog__date').distinct(
            'model_instance_uuid'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deployments = CampaignDetailView._filter_latest_changes(
            Change.objects.of_type(Deployment)
            .filter(
                update__campaign=str(
                    context['object'].model_instance_uuid or self.kwargs[self.pk_url_kwarg]
                )
            )
            .prefetch_approvals()
        )

        collection_periods = CampaignDetailView._filter_latest_changes(
            Change.objects.of_type(CollectionPeriod)
            .filter(update__deployment__in=[str(d.model_instance_uuid) for d in deployments])
            .select_related("content_type")
            .prefetch_approvals()
            .annotate_from_relationship(
                of_type=Platform, uuid_from="platform", to_attr="platform_name"
            )
        )

        # Build collection periods instruments (too difficult to do in SQL)
        instrument_uuids = set()
        for cp in collection_periods:
            for uuid in cp.update["instruments"]:
                instrument_uuids.add(uuid)

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
            # By setting the model name, our nav sidebar knows to highlight the link for campaigns
            'model_name': 'campaign',
            "deployments": deployments,
            "transition_form": forms.TransitionForm(
                change=context["object"], user=self.request.user
            ),
            "significant_events": CampaignDetailView._filter_latest_changes(
                Change.objects.of_type(SignificantEvent)
                .filter(update__deployment__in=[str(d.model_instance_uuid) for d in deployments])
                .select_related("content_type")
                .prefetch_approvals()
            ),
            "iops": CampaignDetailView._filter_latest_changes(
                Change.objects.of_type(IOP)
                .filter(update__deployment__in=[str(d.model_instance_uuid) for d in deployments])
                .select_related("content_type")
                .prefetch_approvals()
            ),
            "collection_periods": collection_periods,
        }


@method_decorator(login_required, name="dispatch")
class ChangeCreateView(
    NotificationSidebar, mixins.DynamicModelMixin, mixins.ChangeModelFormMixin, CreateView
):
    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/change_create.html"

    def get_initial(self):
        # Get initial form values from URL
        return {
            "content_type": self.get_model_form_content_type(),
            "action": (
                Change.Actions.UPDATE if self.request.GET.get("uuid") else Change.Actions.CREATE
            ),
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
            try:
                self.model_form_content_type = ContentType.objects.get_for_model(
                    MODEL_CONFIG_MAP[self._model_name]['model']
                )
            except (KeyError, ContentType.DoesNotExist) as e:
                raise Http404(f'Unsupported model type: {self._model_name}') from e
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
class ChangeUpdateView(NotificationSidebar, mixins.ChangeModelFormMixin, UpdateView):
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/change_update.html"
    queryset = (
        Change.objects.select_related("content_type")
        .prefetch_approvals()
        .annotate_from_relationship(
            of_type=Image, to_attr="logo_path", uuid_from="logo", identifier="image"
        )
    )

    def get_success_url(self):
        url = reverse("change-update", args=[self.object.pk])
        if self.request.GET.get("back"):
            return f'{url}?back={self.request.GET["back"]}'
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            "transition_form": (
                forms.TransitionForm(change=context["object"], user=self.request.user)
            ),
            "campaign_subitems": ["Deployment", "IOP", "SignificantEvent", "CollectionPeriod"],
            "related_fields": self._get_related_fields(),
            "view_model": camel_to_snake(self.get_model_form_content_type().model_class().__name__),
            "ancestors": context["object"].get_ancestors().select_related("content_type"),
            "descendents": context["object"].get_descendents().select_related("content_type"),
            "comparison_form": self._get_comparison_form(context['model_form']),
        }

    def _get_comparison_form(self, model_form):
        """
        Generates a disabled form for the published model, used for generating
        a diff view.
        """
        if self.object.action != self.object.Actions.UPDATE:
            return None

        published_form = self.destination_model_form(
            instance=self.object.content_object, auto_id="readonly_%s"
        )

        # if published or trashed then the old data doesn't need to be from the database, it
        # needs to be from the previous field of the change_object
        if self.object.is_locked:
            for key, val in self.object.previous.items():
                published_form.initial[key] = val

        comparison_obj = self.object.previous if self.object.is_locked else self.object.update
        for field_name in comparison_obj:
            if not utils.compare_values(
                published_form[field_name].value(), model_form[field_name].value()
            ):
                attrs = model_form.fields[field_name].widget.attrs
                attrs["class"] = f"{attrs.get('class', '')} changed-item".strip()

        return utils.disable_form_fields(published_form)

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def _get_related_fields(self) -> Dict:
        related_fields = {}
        content_type = self.get_model_form_content_type().model_class().__name__
        if content_type in ["Campaign", "Platform", "Deployment", "Instrument", "PartnerOrg"]:
            related_fields["alias"] = Change.objects.of_type(Alias).filter(
                update__object_id=str(self.object.uuid)
            )
        if content_type == "Campaign":
            related_fields["website"] = (
                Change.objects.of_type(Website)
                .filter(action=Change.Actions.CREATE, update__campaign=str(self.object.uuid))
                .annotate_from_relationship(
                    of_type=Website, to_attr="title", uuid_from="website", identifier="title"
                )
            )
        return related_fields

    def get_model_form_intial(self):
        return self.object.update

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        if self.object.status == Change.Statuses.PUBLISHED:
            return HttpResponseBadRequest("Unable to submit published records.")
        return super().post(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ChangeListView(NotificationSidebar, mixins.DynamicModelMixin, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"

    def dispatch(self, *args, **kwargs):
        if self._model_config["admin_required_to_view"]:
            authorization_level = user_passes_test(lambda user: user.is_admg_admin())
        else:
            authorization_level = login_required
        return authorization_level(super().dispatch)(*args, **kwargs)

    def get_table_class(self):
        return self._model_config["change_list_table"]

    def get_filterset_class(self):
        return self._model_config["draft_filter"]

    def get_queryset(self):
        queryset = (
            Change.objects.of_type(self._model_config['model'])
            .add_updated_at()
            .order_by("-updated_at")
        )

        if self._model_config['model'] == Platform:
            return queryset.annotate_from_relationship(
                of_type=PlatformType, uuid_from="platform_type", to_attr="platform_type_name"
            )
        else:
            return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "url_name": self._model_config["singular_snake_case"],
            "view_model": self._model_name,
            "display_name": self._model_config["display_name"],
        }

    def post(self, request, **kwargs):
        from cmr import tasks

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
class ChangeTransition(NotificationSidebar, FormMixin, ProcessFormView, DetailView):
    model = Change
    form_class = forms.TransitionForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "change": self.get_object(), "user": self.request.user}

    def form_valid(self, form):
        try:
            form.apply_transition()
        except ValidationError as err:
            messages.error(
                self.request,
                mark_safe(f"<b>Unable to transition draft.</b> {format_validation_error(err)}"),
            )
        else:
            obj = self.get_object()
            messages.success(
                self.request,
                f"Transitioned \"{obj.model_name}: {obj.update.get('short_name', obj.uuid)}\" "
                f"to \"{obj.get_status_display()}\".",
            )

        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER") or super().get_success_url()


def format_validation_error(err: ValidationError) -> str:
    return (
        '<ul class="list-unstyled">'
        + "".join(
            (f"<li>{field}<ul>" + "".join(f"<li>{e}</li>" for e in errors) + "</ul></li>")
            for field, errors in err.detail.items()
        )
        + "</ul>"
    )


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class GcmdSyncListView(NotificationSidebar, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    filterset_class = filters.GcmdSyncListFilter
    table_class = tables.GcmdSyncListTable

    def get_queryset(self):
        resolved_records = Recommendation.objects.filter(
            change_id=OuterRef("uuid"), result__isnull=False
        )

        queryset = (
            (
                Change.objects.of_type(GcmdInstrument, GcmdPlatform, GcmdProject, GcmdPhenomenon)
                .select_related("content_type")
                .annotate(
                    short_name=functions.Coalesce(
                        *[
                            functions.NullIf(KeyTextTransform(attr, dictionary), Value(""))
                            for attr in gcmd.short_name_priority
                            for dictionary in ["update", "previous"]
                        ]
                    ),
                    resolved_records=functions.Coalesce(SubqueryCount(resolved_records), Value(0)),
                    affected_records=Count("recommendation", distinct=True),
                )
                .filter(Q(recommendation__submitted=False) | Q(status__lte=5))
            )
            .add_updated_at()
            .order_by("-updated_at")
        )

        return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "GCMD Keyword",
            "current_view": "gcmd-list",
        }

    def post(self, request, **kwargs):
        from kms import tasks

        task = tasks.sync_gcmd.delay()
        logger.debug(f"Task return value: {task}")
        messages.add_message(request, messages.INFO, "Syncing with GCMD...")
        return HttpResponseRedirect(reverse('gcmd-list'))


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class ChangeGcmdUpdateView(NotificationSidebar, UpdateView):
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/change_gcmd.html"
    queryset = Change.objects.select_related("content_type").prefetch_approvals()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            **context,
            "transition_form": (
                forms.TransitionForm(change=context["object"], user=self.request.user)
            ),
            "gcmd_path": gcmd.get_gcmd_path(self.object),
            "affected_records": self.get_affected_records(),
            "back_button": self.get_back_button_url(),
            "action": self.object.action,
            "short_name": gcmd.get_short_name(self.object),
            "ancestors": (context["object"].get_ancestors().select_related("content_type")),
            "descendents": (context["object"].get_descendents().select_related("content_type")),
            "view_model": camel_to_snake(self.object.content_type.model_class().__name__),
        }
        return context

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_affected_type(self):
        content_type = self.get_model_form_content_type().model_class().__name__
        casei_type = gcmd.get_casei_model(content_type)
        return casei_type.__name__

    def get_affected_url(self, uuid):
        content_type = self.get_model_form_content_type().model_class().__name__
        casei_model_name = gcmd.get_casei_model(content_type)
        return {
            "model": casei_model_name.__name__.lower(),
            "casei_uuid": uuid,
        }

    def is_connected(self, gcmd_keyword, casei_object, content_type):
        if gcmd_keyword.action == Change.Actions.CREATE:
            return "New Keyword"
        else:
            keyword_set = gcmd.get_casei_keyword_set(casei_object, content_type)
            is_connnected = gcmd_keyword.content_object in keyword_set.all()
            return "Yes" if is_connnected else "No"

    def get_affected_records(self) -> Dict:
        content_type = self.get_model_form_content_type().model_class().__name__
        recommendations = Recommendation.objects.filter(change_id=self.object.uuid)
        category = self.get_affected_type()
        affected_records, uuids = [], []

        for recommendation in recommendations:
            uuids.append(str(recommendation.casei_object.uuid))
            affected_records.append(
                {
                    "row": recommendation.casei_object,
                    "status": "Published",
                    "category": category,
                    "link": self.get_affected_url(recommendation.casei_object.uuid),
                    "is_connected": self.is_connected(
                        self.object, recommendation.casei_object, content_type
                    ),
                    "current_selection": recommendation.result,
                    "is_submitted": recommendation.submitted,
                    "uuids": uuids,
                }
            )
        return affected_records

    def get_back_button_url(self):
        return "gcmd-list"

    def get_casei_object(self, uuid, content_type):
        casei_model = gcmd.get_casei_model(content_type)
        return casei_model.objects.get(uuid=uuid)

    def process_choice(self, choice_uuid, decision_dict, request_type="Save"):
        gcmd_change = self.get_object()
        change_action = gcmd_change.action
        recommendation = Recommendation.objects.get(object_uuid=choice_uuid, change=gcmd_change)

        # Save the user's input for both save and publish buttons
        if change_action == Change.Actions.DELETE or decision_dict.get(choice_uuid) == "False":
            recommendation.result = False
        elif decision_dict.get(choice_uuid) == "True":
            recommendation.result = True
        elif decision_dict.get(choice_uuid) is None:
            recommendation.result = None
        recommendation.save()

        if request_type == "Publish":
            content_type = gcmd_change.content_type.model_class().__name__
            gcmd_keyword = gcmd_change.content_object
            casei_object = self.get_casei_object(choice_uuid, content_type)
            keyword_set = gcmd.get_casei_keyword_set(casei_object, content_type)

            if change_action == Change.Actions.DELETE or decision_dict.get(choice_uuid) == "False":
                recommendation.result = False
                recommendation.submitted = True
                keyword_set.remove(gcmd_keyword)
            elif decision_dict.get(choice_uuid) == "True":
                recommendation.result = True
                recommendation.submitted = True
                keyword_set.add(gcmd_keyword)

            # Change Resolved list to "Submitted" and save all database changes.
            casei_object.save()
            recommendation.save()

    def publish_keyword(self, user):
        gcmd_change = self.get_object()
        # Publish the keyword, Create keywords are automatically "Published" so skip them.
        if not gcmd_change.action == Change.Actions.CREATE:
            gcmd_change.publish(user=user)

    def post(self, request, **kwargs):
        import ast

        choices = {
            x.replace("choice-", ""): request.POST[x]
            for x in request.POST
            if x.startswith("choice-")
        }
        for casei_uuid in ast.literal_eval(request.POST.get("related_uuids", "[]")):
            self.process_choice(casei_uuid, choices, request.POST.get("user_button", "Save"))

        # After all connections are made (or ignored), let's finally publish the keyword!
        if request.POST.get("user_button") == "Publish":
            self.publish_keyword(request.user)

            messages.success(
                request,
                f'Successfully published GCMD Keyword "{gcmd.get_short_name(self.get_object())}"',
            )
            return HttpResponseRedirect(reverse("gcmd-list"))
        else:
            messages.success(
                request,
                f'Successfully saved progress for "{gcmd.get_short_name(self.get_object())}"',
            )
            return HttpResponseRedirect(reverse("change-gcmd", args=[kwargs["pk"]]))
