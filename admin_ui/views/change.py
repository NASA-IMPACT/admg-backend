from typing import Dict

import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import aggregates, functions, OuterRef, Value, Subquery
from django.db.models.fields.json import KeyTextTransform
from django.db.models import IntegerField, Count, F, Q
from django.db.utils import ProgrammingError

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormMixin, ProcessFormView, UpdateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from rest_framework.serializers import ValidationError


from admin_ui.config import MODEL_CONFIG_MAP
from api_app.models import ApprovalLog, Change, ResolvedList, Recommendation, SubqueryCount
from data_models.models import (
    IOP,
    Alias,
    Campaign,
    CollectionPeriod,
    Deployment,
    GcmdInstrument,
    GcmdPhenomena,
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


class GcmdCounts:
    def get_gcmd_count(self):
        return (
            Change.objects.of_type(GcmdInstrument, GcmdPlatform, GcmdProject, GcmdPhenomena)
            .select_related("content_type", "resolvedlist")
            .filter(resolvedlist__submitted=False)
            .count()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            **context,
            "gcmd_changes_count": self.get_gcmd_count(),
        }
        print(f"CONTEXT DATA: {context}")
        return context


@method_decorator(login_required, name="dispatch")
class SummaryView(GcmdCounts, django_tables2.SingleTableView):
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
                self.model_form_content_type = ContentType.objects.get(
                    app_label="data_models", model__iexact=self.kwargs["model"]
                )
            except ContentType.DoesNotExist as e:
                raise Http404(f'Unsupported model type: {self.kwargs["model"]}') from e
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


# TODO: Change this back
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
        url = (
            reverse("change-diff", args=[self.object.pk])
            if self.object.action == Change.Actions.UPDATE
            else reverse("change-update", args=[self.object.pk])
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
            "related_fields": self.get_related_fields(),
            "back_button": self.get_back_button_url(),
            "ancestors": (context["object"].get_ancestors().select_related("content_type")),
            "descendents": (context["object"].get_descendents().select_related("content_type")),
        }

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_related_fields(self) -> Dict:
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
            "Website": "website-list-draft",
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


@method_decorator(login_required, name="dispatch")
class DiffView(ChangeUpdateView):
    model = Change
    template_name = "api_app/change_diff.html"

    def _compare_forms_and_format(self, updated_form, original_form, field_names_to_compare):
        for field_name in field_names_to_compare:
            if not utils.compare_values(
                original_form[field_name].value(), updated_form[field_name].value()
            ):
                attrs = updated_form.fields[field_name].widget.attrs
                attrs["class"] = f"{attrs.get('class', '')} changed-item".strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination_model_instance = context["object"].content_object

        published_form = self.destination_model_form(
            instance=destination_model_instance, auto_id="readonly_%s"
        )
        is_published_or_trashed = (
            context["object"].status == Change.Statuses.PUBLISHED
            or context["object"].status == Change.Statuses.IN_TRASH
        )

        # if published or trashed then the old data doesn't need to be from the database, it
        # needs to be from the previous field of the change_object
        if is_published_or_trashed:
            for key, val in context["object"].previous.items():
                published_form.initial[key] = val

            self._compare_forms_and_format(
                context["model_form"], published_form, context["object"].previous
            )
        else:
            self._compare_forms_and_format(
                context["model_form"], published_form, context["object"].update
            )

        return {
            **context,
            "noneditable_published_form": utils.disable_form_fields(published_form),
            "disable_save": is_published_or_trashed,
        }


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
                Change.objects.of_type(self.linked_model).add_updated_at().order_by("-updated_at")
            )

            if self.linked_model == Platform:
                return queryset.annotate_from_relationship(
                    of_type=PlatformType, uuid_from="platform_type", to_attr="platform_type_name"
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
class GcmdSyncListView(GcmdCounts, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    filterset_class = filters.GcmdSyncFilter
    table_class = tables.GcmdKeywordsListTable

    def get_queryset(self):
        resolved_records = Recommendation.objects.filter(
            resolved_log_id=OuterRef("resolvedlist"), result__isnull=False
        )

        # TODO: Add database migration to create index on content_type.model field and aliases.short_name
        queryset = (
            Change.objects.of_type(GcmdInstrument, GcmdPlatform, GcmdProject, GcmdPhenomena)
            .select_related("content_type", "resolvedlist")
            .annotate(
                short_name=functions.Coalesce(
                    functions.NullIf(KeyTextTransform('short_name', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_3', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_2', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_1', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('term', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('short_name', 'previous'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_3', 'previous'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_2', 'previous'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_1', 'previous'), Value("")),
                    functions.NullIf(KeyTextTransform('term', 'previous'), Value("")),
                ),
                resolved_records=functions.Coalesce(SubqueryCount(resolved_records), Value(0)),
                affected_records=Count("resolvedlist__recommendation"),
            )
            .filter(resolvedlist__submitted=False)
            # .add_updated_at()   # TODO: Figure out why this was affecting the affected/resolved counts.
            # .order_by("-updated_at")
        )

        return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            # TODO: Set this, displays at top of page.
            "display_name": "GCMD Keyword",
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class ChangeGcmdUpdateView(GcmdCounts, UpdateView):
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/change_gcmd.html"
    queryset = Change.objects.select_related("content_type").prefetch_approvals()

    def get_context_data(self, **kwargs):
        # print(f"CONTEXT CONTENT OBJECT: {self.object}")
        # print(f"CONTEXT CONTENT TYPE: {type(self.object)}")
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
        }
        return context

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_affected_type(self):
        content_type = self.get_model_form_content_type().model_class().__name__
        casei_type = gcmd.get_casei_model(content_type)
        return casei_type.__name__

    def get_gcmd_path(self) -> Dict:
        path_order = {
            "GcmdPlatform": ["category", "series_entry", "short_name"],
            "GcmdProject": ["bucket", "short_name"],
            "GcmdInstrument": [
                "instrument_category",
                "instrument_class",
                "instrument_type",
                "instrument_subtype",
                "short_name",
            ],
            "GcmdPhenomena": [
                "category",
                "topic",
                "term",
                "variable_1",
                "variable_2",
                "variable_3",
            ],
        }

        def get_initial_path(action):
            path = {"path": []}
            if self.object.action == Change.Actions.UPDATE:
                path["old_path"], path["new_path"] = True, True
            elif self.object.action == Change.Actions.DELETE:
                path["old_path"], path["new_path"] = True, False
            elif self.object.action == Change.Actions.CREATE:
                path["old_path"], path["new_path"] = False, True
            return path

        def format_path_keys(key):
            return key.replace("_", " ").title()

        def replace_empty_path_values(value):
            return "[NO VALUE]" if value in ["", " "] else value

        def compare_gcmd_path_attribute(attribute, new_object, previous_object={}):
            return {
                "key": format_path_keys(attribute),
                "old_value": replace_empty_path_values(
                    previous_object.get(attribute, "[NO VALUE]")
                    if previous_object is not {}
                    else '[NO VALUE]'
                ),
                "new_value": replace_empty_path_values(new_object.get(attribute, '')),
                "has_changed": previous_object is {}
                or new_object is {}
                or not previous_object.get(attribute) == new_object.get(attribute),
            }

        content_type = self.get_model_form_content_type().model_class().__name__
        path = get_initial_path(self.object.action)

        path_order = gcmd.get_path_order(content_type)
        for attribute in path_order:
            path["path"].append(
                compare_gcmd_path_attribute(attribute, self.object.update, self.object.previous)
            )
        return path

    # TODO: Change links to active_links in Django Template
    def get_affected_url(self, uuid):
        content_type = self.get_model_form_content_type().model_class().__name__
        casei_model_name = gcmd.get_casei_model(content_type)
        return f"/{casei_model_name.__name__.lower()}s/published/{uuid}"

    def is_connected(self, gcmd_keyword, casei_object, content_type):
        if gcmd_keyword.action == Change.Actions.CREATE:
            return "New Keyword"
        else:
            keyword_set = gcmd.get_casei_keyword_set(casei_object, content_type)
            is_connnected = gcmd_keyword.content_object in keyword_set.all()
            return "Yes" if is_connnected else "No"

    # TODO: There is probably a better way of doing this.
    def get_current_selection(self, keyword, casei_object, resolved_list):
        recommendation = Recommendation.objects.get(
            object_uuid=casei_object.uuid, resolved_log=resolved_list
        )
        result = recommendation.result
        if result is None:
            return {}
        elif result:
            return {"connect": True}
        else:
            return {"ignore": True}

    def get_affected_records(self) -> Dict:
        content_type = self.get_model_form_content_type().model_class().__name__
        # TODO: Add Exception in case this doesn't exist!
        # Idea: Probably tell them name of keyword but show message with error telling them
        #       to reach out to admin to fix problem.
        resolved_list = ResolvedList.objects.get(change_id=self.object.uuid)
        category = self.get_affected_type()
        # TODO: Make this better
        affected_records, uuids = [], []

        for row in resolved_list.recommendation_set.all():
            uuids.append(str(row.parent_fk.uuid))
            affected_records.append(
                {
                    "row": row.parent_fk,
                    "status": "Published",
                    "category": category,
                    "link": self.get_affected_url(row.parent_fk.uuid),
                    "is_connected": self.is_connected(self.object, row.parent_fk, content_type),
                    "currentSelection": self.get_current_selection(
                        self.object, row.parent_fk, resolved_list
                    ),
                    "is_submitted": resolved_list.submitted,
                    "uuids": uuids,  # TODO: Put the uuids somewhere else
                }
            )
        return affected_records

    def get_back_button_url(self):
        return "review_changes-list-draft"

    def get_casei_object(self, uuid, content_type):
        casei_model = gcmd.get_casei_model(content_type)
        return casei_model.objects.get(uuid=uuid)

    # TODO: Clean this method up.
    def post(self, request, **kwargs):
        # TODO: Remove import and clean up method
        import ast

        gcmd_change = self.get_object()
        resolved_list = ResolvedList.objects.get(change_id=gcmd_change.uuid)
        choices = {
            x.replace("choice-", ""): request.POST[x]
            for x in request.POST
            if x.startswith("choice-")
        }
        for valid_uuid in ast.literal_eval(request.POST["related_uuids"]):
            recommendation = Recommendation.objects.get(
                object_uuid=valid_uuid, resolved_log=resolved_list
            )

            if choices.get(valid_uuid) is None:
                recommendation.result = None
            elif choices.get(valid_uuid) == "True":
                recommendation.result = True
            elif choices.get(valid_uuid) == "False":
                recommendation.result = False
            recommendation.save()

            # print("POST REQUEST: ", request.POST)
            if request.POST.get("user_button") == "Publish":
                print("Post request is for Publish")
                content_type = gcmd_change.content_type.model_class().__name__
                casei_object = self.get_casei_object(valid_uuid, content_type)
                gcmd_keyword = gcmd_change._get_model_instance()
                keyword_set = gcmd.get_casei_keyword_set(casei_object, content_type)
                # print(f"KEYWORD CONTENT TYPE: {type(content_type)}, {content_type}")
                # print(f"Keyword Set: {type(keyword_set)}, {keyword_set}")

                if choices.get(valid_uuid) == "True":
                    recommendation.result = True
                    keyword_set.add(gcmd_keyword)

                elif choices.get(valid_uuid) == "False":
                    recommendation.result = False
                    keyword_set.remove(gcmd_keyword)

                # Change Resolved list to "Submitted" and save all database changes.
                resolved_list.save()
                casei_object.save()
                recommendation.save()

        # After all connections are made, let's finally publish the keyword!
        # TODO: Put this in a seperate function.
        # TODO: Put notes in publish method.
        # TODO: Maybe check to see if response is valid and maybe show user errors in any
        if request.POST.get("user_button") == "Publish":
            resolved_list.submitted = True
            resolved_list.save()
            # Publish the keyword, Create keywords are automatically "Published" so skip them.
            if not gcmd_change.action == Change.Actions.CREATE:
                response = gcmd_change.publish(user=request.user)

        return HttpResponseRedirect(reverse("change-gcmd", args=[kwargs["pk"]]))
