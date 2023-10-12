from typing import Dict

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.forms import modelform_factory
import django_tables2 as tables
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.views.generic.edit import UpdateView
from django.db.models import Q, OuterRef, Subquery
from django.views.generic.edit import CreateView
from admin_ui.config import MODEL_CONFIG_MAP

from admin_ui.views.published import ModelObjectView

from api_app.models import Change
from data_models.models import (
    IOP,
    Alias,
    Campaign,
    CollectionPeriod,
    Deployment,
    Instrument,
    Platform,
    PlatformType,
    SignificantEvent,
    Website,
)
from .. import forms, mixins, utils
from api_app.views.generic_views import NotificationSidebar
from api_app.urls import camel_to_snake
from ..tables import DraftHistoryTable


# TODO add login requirement
def redirect_helper(request, canonical_uuid, draft_uuid, model):
    try:
        has_progress_draft = (
            Change.objects.exclude(status=Change.Statuses.PUBLISHED)
            .filter(Q(uuid=canonical_uuid) | Q(model_instance_uuid=canonical_uuid))
            .exists()
        )
        if not has_progress_draft:
            return redirect(
                reverse(
                    "canonical-published-detail",
                    kwargs={
                        "canonical_uuid": canonical_uuid,
                        "model": model,
                        "draft_uuid": draft_uuid,
                    },
                )
            )
        return redirect(
            reverse(
                "canonical-draft-edit",
                kwargs={
                    "canonical_uuid": canonical_uuid,
                    "model": model,
                },
            )
        )
    except Change.DoesNotExist:
        raise Http404("Canonical UI does not exist")


# Lists all the canonical records for a given model type
@method_decorator(login_required, name="dispatch")
class CanonicalRecordList(mixins.DynamicModelMixin, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/canonical/change_list.html"

    def get_table_class(self):
        return self._model_config["change_list_table"]

    def get_filterset_class(self):
        return self._model_config["draft_filter"]

    def get_queryset(self):
        """
        We are getting a list of all created records (so we can link to them).
        However, we want to display the most recent related draft in the table.
        """
        # find the most recent drafts for each canonical CREATED draft
        related_drafts = Change.objects.filter(
            Q(model_instance_uuid=OuterRef("uuid")) | Q(uuid=OuterRef("uuid"))
        ).order_by("status", "-updated_at")

        latest_published_draft = Change.objects.filter(
            status=Change.Statuses.PUBLISHED,
            model_instance_uuid=OuterRef("uuid"),
        ).order_by("-updated_at")

        queryset = (
            (
                Change.objects.filter(action=Change.Actions.CREATE).of_type(
                    self._model_config['model']
                )
            )
            .annotate(
                draft_uuid=Subquery(related_drafts.values("uuid")[:1]),
                latest_status=Subquery(related_drafts.values("status")[:1]),
                latest_action=Subquery(related_drafts.values("action")[:1]),
                latest_updated_at=Subquery(related_drafts.values("updated_at")[:1]),
                latest_published_at=Subquery(latest_published_draft.values("updated_at")[:1]),
                latest_update=Subquery(related_drafts.values("update")[:1]),
            )
            .order_by("-latest_updated_at")
        )

        if self._model_config['model'] == Platform:
            return queryset.annotate_from_relationship(
                of_type=PlatformType, uuid_from="platform_type", to_attr="platform_type_name"
            )
        return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "url_name": self._model_config["singular_snake_case"],
            "view_model": self._model_name,
            "display_name": self._model_config["display_name"],
        }


@method_decorator(login_required, name="dispatch")
class ChangeHistoryList(mixins.DynamicModelMixin, tables.SingleTableView):
    model = Change
    table_class = DraftHistoryTable
    pk_url_kwarg = 'canonical_uuid'
    template_name = "api_app/canonical/change_history.html"

    def get_queryset(self):
        return Change.objects.filter(
            Q(model_instance_uuid=self.kwargs[self.pk_url_kwarg])
            | Q(uuid=self.kwargs[self.pk_url_kwarg])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view_model = Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name.lower()
        return {
            **context,
            "view_model": view_model,
            "object": Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]),
            "canonical_uuid": self.kwargs[self.pk_url_kwarg],
        }


class HistoryDetailView(ModelObjectView):
    model = Change
    pk_url_kwarg = 'draft_uuid'
    template_name = "api_app/canonical/historical_detail.html"
    pk_url_kwarg = 'canonical_uuid'
    fields = ["content_type", "model_instance_uuid", "action", "update"]

    def get_model_form_content_type(self) -> ContentType:
        return Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).content_type

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "model_form": self._get_form(instance=kwargs.get("object"), disable_all=True),
            "view_model": (
                Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name.lower()
            ),
            "object": Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]),
            "display_name": Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name,
            "canonical_uuid": self.kwargs[self.pk_url_kwarg],
        }


@method_decorator(login_required, name="dispatch")
class CanonicalRecordPublished(ModelObjectView):
    model = Change
    pk_url_kwarg = 'canonical_uuid'
    template_name = "api_app/canonical/published_detail.html"
    fields = ["content_type", "model_instance_uuid", "action", "update"]

    def get_model_form_content_type(self) -> ContentType:
        return Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).content_type

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            "model_form": self._get_form(instance=kwargs.get("object"), disable_all=True),
            "view_model": (
                Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name.lower()
            ),
            "display_name": Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name,
            "has_progress_draft": (
                Change.objects.exclude(status=Change.Statuses.PUBLISHED)
                .filter(
                    Q(uuid=self.kwargs[self.pk_url_kwarg])
                    | Q(model_instance_uuid=self.kwargs[self.pk_url_kwarg])
                )
                .exists()
            ),
        }


@method_decorator(login_required, name="dispatch")
class CanonicalDraftEdit(NotificationSidebar, mixins.ChangeModelFormMixin, UpdateView):
    """This view is in charge of editing existing drafts.
    If the draft has a related published record, a diff view is returned to the user.
    Otherwise a single form view is returned.
    """

    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/canonical/change_update.html"
    pk_url_kwarg = 'canonical_uuid'
    queryset = Change.objects.all().exclude(status=Change.Statuses.PUBLISHED)

    def get_queryset(self):
        return Change.objects.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        has_progress_draft = (
            Change.objects.exclude(status=Change.Statuses.PUBLISHED)
            .filter(
                model_instance_uuid=self.canonical_change.uuid,
                content_type=self.canonical_change.content_type,
                action=Change.Actions.UPDATE,
            )
            .exists()
        )

        has_published_draft = Change.objects.filter(
            Q(uuid=self.canonical_change.uuid) | Q(model_instance_uuid=self.canonical_change.uuid),
            status=Change.Statuses.PUBLISHED,
        ).exists()

        if not has_progress_draft and has_published_draft:
            return redirect(
                reverse(
                    "canonical-published-detail",
                    kwargs={
                        "canonical_uuid": self.kwargs[self.pk_url_kwarg],
                        "draft_uuid": self.object.pk,
                        "model": self.kwargs["model"],
                    },
                )
            )
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.queryset

        canonical_uuid = self.kwargs["canonical_uuid"]
        return (
            queryset.filter(Q(uuid=canonical_uuid) | Q(model_instance_uuid=canonical_uuid))
            .order_by('status')
            .first()
        )

    def get_success_url(self, **kwargs):
        url = reverse(
            "canonical-redirect",
            kwargs={
                "canonical_uuid": self.kwargs[self.pk_url_kwarg],
                "draft_uuid": self.object.pk,
                "model": self.kwargs["model"],
            },
        )
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
            "canonical_uuid": self.kwargs[self.pk_url_kwarg],
            "draft_uuid": self.object.pk,
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

        comparison_obj = self.destination_model_form(
            data=self.object.previous if self.object.is_locked else self.object.update
        )
        for field_name in comparison_obj.fields:
            if not utils.compare_values(
                published_form[field_name].value(), model_form[field_name].value()
            ):
                attrs = model_form.fields[field_name].widget.attrs
                attrs["class"] = f"{attrs.get('class', '')} changed-item".strip()

        return utils.disable_form_fields(published_form)

    def get_model_form_content_type(self) -> ContentType:
        return self.get_object().content_type

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
class CreateNewView(mixins.DynamicModelMixin, mixins.ChangeModelFormMixin, CreateView):
    """
    This view handles creating brand new drafts.
    """

    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/canonical/change_create.html"

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
            "view_model": self._model_name,
        }

    def get_success_url(self):
        return reverse(
            "canonical-draft-edit",
            kwargs={
                "canonical_uuid": self.object.pk,
                "model": self._model_name,
            },
        )

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
class CreateUpdateView(mixins.DynamicModelMixin, mixins.ChangeModelFormMixin, CreateView):
    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/canonical/change_update.html"
    pk_url_kwarg = 'canonical_uuid'

    def get_initial(self):
        # Get initial form values from URL
        return {
            "content_type": self.get_model_form_content_type(),
            "action": (Change.Actions.UPDATE),
            "model_instance_uuid": self.kwargs["canonical_uuid"],
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **super().get_context_data(**kwargs),
            "content_type_name": (self.get_model_form_content_type().model_class().__name__),
            "comparison_form": self._get_comparison_form(context['model_form']),
            "object": self.object,
            "canonical_uuid": self.kwargs[self.pk_url_kwarg],
            "view_model": (
                Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name.lower()
            ),
            "display_name": Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg]).model_name,
            "draft_uuid": self.object.pk,
        }

    def get_success_url(self):
        return reverse(
            "canonical-draft-edit",
            kwargs={
                "model": self._model_name,
                "canonical_uuid": self.kwargs["canonical_uuid"],
            },
        )

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
        # return {k: v for k, v in self.request.GET.dict().items() if k != "uuid"}

        # 0 get model
        Model = self._model_config["model"]
        # 1 get published record
        published_record = Model.objects.get(uuid=self.kwargs["canonical_uuid"])
        # 2 serialize published record into dictonary
        # 2.1 Find the model form
        ModelForm = modelform_factory(Model, exclude=[])
        # 2.2 create form
        form = ModelForm(instance=published_record)

        return form.initial

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        self.canonical_change = queryset.get(uuid=self.kwargs["canonical_uuid"])

        # if the canonical record is not published, return the record itself
        if self.canonical_change.status != Change.Statuses.PUBLISHED:
            return self.canonical_change

        # TODO: include uuid in url instead of looking up the record again
        # create a new update draft from most recently published draft
        most_recent_published_draft = (
            Change.objects.filter(
                status=Change.Statuses.PUBLISHED,
                model_instance_uuid=self.kwargs["canonical_uuid"],
            )
            .order_by("updated_at")
            .last()
        )

        most_recent_published_draft.status = Change.Statuses.CREATED
        most_recent_published_draft.action = Change.Actions.UPDATE
        most_recent_published_draft.update = most_recent_published_draft.update
        most_recent_published_draft.previous = most_recent_published_draft.update

        return most_recent_published_draft

    def _get_comparison_form(self, model_form):
        """
        Generates a disabled form for the published model, used for generating
        a diff view.
        """
        self.object = self.get_object()
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

        comparison_obj = self.destination_model_form(
            data=self.object.previous if self.object.is_locked else self.object.update
        )
        for field_name in comparison_obj.fields:
            if not utils.compare_values(
                published_form[field_name].value(), model_form[field_name].value()
            ):
                attrs = model_form.fields[field_name].widget.attrs
                attrs["class"] = f"{attrs.get('class', '')} changed-item".strip()

        return utils.disable_form_fields(published_form)

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = None
        return super().post(*args, **kwargs)


class CampaignDetailView(NotificationSidebar, DetailView):
    model = Change
    template_name = "api_app/canonical/campaign_details.html"
    queryset = Change.objects.of_type(Campaign)

    def get_queryset(self):
        return Change.objects.all()

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        self.canonical_draft = queryset.get(uuid=self.kwargs["canonical_uuid"])

        unpublished_draft = Change.objects.exclude(
            status=Change.Statuses.PUBLISHED,
        ).filter(model_instance_uuid=self.kwargs["canonical_uuid"])

        most_recent_published_draft = Change.objects.filter(
            status=Change.Statuses.PUBLISHED,
            model_instance_uuid=self.kwargs["canonical_uuid"],
        ).order_by("updated_at")

        return (
            unpublished_draft.first() or most_recent_published_draft.last() or self.canonical_draft
        )

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
                    context['object'].model_instance_uuid or self.kwargs["canonical_uuid"]
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
            # By setting the view model, our nav sidebar knows to highlight the link for campaigns
            'view_model': 'campaign',
            'canonical_object': self.canonical_draft,
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
