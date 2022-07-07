from typing import Dict

import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import aggregates
from django.http import Http404, HttpResponseBadRequest
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormMixin, ProcessFormView, UpdateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from rest_framework.serializers import ValidationError

from admin_ui.config import MODEL_CONFIG_MAP
from api_app.models import ApprovalLog, Change
from api_app.urls import camel_to_snake
from data_models.models import (
    IOP,
    Alias,
    Campaign,
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

from .. import forms, mixins, tables, utils


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

    def get_total_counts(self):
        # TODO: Figure out if the total count should be total showing casei or total Change.
        # This would be total "Published" items in CASEI
        return {
            model.__name__.lower(): Change.objects.of_type(model)
            .filter(action=Change.Actions.CREATE)
            .count()
            for model in self.models
        }

    def get_draft_status_count(self):
        status_ids = [
            Change.Statuses.CREATED,
            Change.Statuses.IN_PROGRESS,
            Change.Statuses.IN_REVIEW,
            Change.Statuses.IN_ADMIN_REVIEW,
            Change.Statuses.PUBLISHED,
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
            .filter(action=Change.Actions.CREATE, status__in=status_ids)  # TODO: Document this.
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
            # "total_counts": {"campaign": None, "platform": None, "instrument": None},
            "total_counts": self.get_total_counts(),
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
            .filter(
                update__campaign=str(
                    context['object'].model_instance_uuid or self.kwargs[self.pk_url_kwarg]
                )
            )
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
            for instruments in collection_periods.values_list("update__instruments", flat=True)
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
            # By setting the model name, our nav sidebar knows to highlight the link for campaigns
            'model_name': 'campaign',
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
class ChangeCreateView(mixins.DynamicModelMixin, mixins.ChangeModelFormMixin, CreateView):
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
class ChangeUpdateView(mixins.ChangeModelFormMixin, UpdateView):
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
class ChangeListView(mixins.DynamicModelMixin, SingleTableMixin, FilterView):
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


@method_decorator(login_required, name="dispatch")
class ChangeTransition(FormMixin, ProcessFormView, DetailView):
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
                (
                    f"Transitioned \"{obj.model_name}: {obj.update.get('short_name', obj.uuid)}\" "
                    f'to "{obj.get_status_display()}".'
                ),
            )

        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER") or super().get_success_url()


def format_validation_error(err: ValidationError) -> str:
    return (
        '<ul class="list-unstyled">'
        + "".join(
            (f"<li>{field}" "<ul>" + "".join(f"<li>{e}</li>" for e in errors) + "</ul>" "</li>")
            for field, errors in err.detail.items()
        )
        + "</ul>"
    )
