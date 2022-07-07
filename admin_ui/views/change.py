from typing import Dict

import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import aggregates, functions, OuterRef, Value, Count
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
    GcmdProject,
    GcmdPlatform,
    Image,
    Instrument,
    PartnerOrg,
    Platform,
    PlatformType,
    SignificantEvent,
    Website,
)

from .. import forms, mixins, tables, utils, filters

from kms import gcmd


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

    def get_draft_status_count(self):
        status_ids = [
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
            .filter(action=Change.Actions.CREATE, status__in=status_ids)
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


class CampaignDetailView(NotificationSidebar, DetailView):
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


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class GcmdSyncListView(NotificationSidebar, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    filterset_class = filters.GcmdSyncFilter
    table_class = tables.GcmdKeywordsListTable

    def get_queryset(self):
        resolved_records = Recommendation.objects.filter(
            change_id=OuterRef("uuid"), result__isnull=False
        )

        queryset = (
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
            .filter(recommendation__submitted=False)
        )

        return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "GCMD Keyword",
            "current_view": "gcmd-list",
        }


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
            "gcmd_path": self.get_gcmd_path(),
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

    def _create_initial_path_dict(self):
        path = {"path": []}
        if self.object.action == Change.Actions.UPDATE:
            path["old_path"], path["new_path"] = True, True
        elif self.object.action == Change.Actions.DELETE:
            path["old_path"], path["new_path"] = True, False
        elif self.object.action == Change.Actions.CREATE:
            path["old_path"], path["new_path"] = False, True
        return path

    def _format_path_keys(self, key):
        return key.replace("_", " ").title()

    def _replace_empty_path_values(self, value):
        return "[NO VALUE]" if value in ["", " "] else value

    def compare_gcmd_path_attribute(self, attribute, new_object, previous_object={}):
        return {
            "key": self._format_path_keys(attribute),
            "old_value": self._replace_empty_path_values(
                previous_object.get(attribute, "[NO VALUE]")
                if previous_object is not {}
                else '[NO VALUE]'
            ),
            "new_value": self._replace_empty_path_values(new_object.get(attribute, '')),
            "has_changed": previous_object is {}
            or new_object is {}
            or not previous_object.get(attribute) == new_object.get(attribute),
        }

    def get_gcmd_path(self) -> Dict:
        path = self._create_initial_path_dict()
        path_order = self.object.content_type.model_class().gcmd_path
        for attribute in path_order:
            path["path"].append(
                self.compare_gcmd_path_attribute(
                    attribute, self.object.update, self.object.previous
                )
            )
        return path

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
        for casei_uuid in ast.literal_eval(request.POST["related_uuids"]):
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
