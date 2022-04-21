from typing import Dict

import django_tables2
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.db.models import aggregates, functions, OuterRef, Value
from django.db.models.fields.json import KeyTextTransform
from django.db.models import IntegerField

# TODO: Figure out if we need this for comparing updates to gcmd objects
from django.forms.models import model_to_dict
from django.http import Http404
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
        context = {
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
        print(f"Context Data: {context}")
        return context

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
class GcmdSyncListView(SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"
    filterset_class = filters.GcmdSyncFilter
    table_class = tables.GcmdKeywordsListTable
    # linked_model = MODEL_CONFIG_MAP[model_name]["model"]

    def get_queryset(self):
        from django.db.models import Func

        affected_campaigns = (
            Campaign.objects.filter(aliases__short_name=OuterRef("short_name"))
            .annotate(count=Func("uuid", function='Count'))
            .values('count')
        )
        affected_instruments = (
            Instrument.objects.filter(aliases__short_name=OuterRef("short_name"))
            .annotate(count=Func("uuid", function='Count'))
            .values('count')
        )
        affected_platforms = (
            Platform.objects.filter(aliases__short_name=OuterRef("short_name"))
            .annotate(count=Func("uuid", function='Count'))
            .values('count')
        )
        # resolved_campaigns = (
        #     Campaign.objects.filter(aliases__short_name=OuterRef("short_name"))
        #     .annotate(count=Func("uuid", function='Count'))
        #     .values('count')
        # )
        # resolved_instruments = (
        #     Instrument.objects.filter(aliases__short_name=OuterRef("short_name"))
        #     .annotate(count=Func("uuid", function='Count'))
        #     .values('count')
        # )
        # resolved_platforms = (
        #     Platform.objects.filter(aliases__short_name=OuterRef("short_name"))
        #     .annotate(count=Func("uuid", function='Count'))
        #     .values('count')
        # )

        # TODO: Add migration to create index on content_type.model field and aliases.short_name
        queryset = (
            Change.objects.of_type(GcmdInstrument, GcmdPlatform, GcmdProject, GcmdPhenomena)
            .select_related("content_type")
            .annotate(
                short_name=functions.Coalesce(
                    functions.NullIf(KeyTextTransform('short_name', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_3', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_2', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('variable_1', 'update'), Value("")),
                    functions.NullIf(KeyTextTransform('term', 'update'), Value("")),
                ),
                affected_campaigns=affected_campaigns,
                affected_instruments=affected_instruments,
                affected_platforms=affected_platforms,
                affected_records=functions.Coalesce(
                    "affected_campaigns",
                    "affected_instruments",
                    "affected_platforms",
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
            .filter(affected_records__gte=1)
            .add_updated_at()
            .order_by("-updated_at")
        )

        return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "GCMD Keyword",
        }


@method_decorator(user_passes_test(lambda user: user.is_admg_admin()), name="dispatch")
class ChangeGcmdUpdateView(mixins.ChangeModelFormMixin, UpdateView):
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]
    prefix = "change"
    template_name = "api_app/change_gcmd.html"
    queryset = Change.objects.select_related("content_type").prefetch_approvals()

    # def get_success_url(self):
    #     url = (
    #         reverse("change-diff", args=[self.object.pk])
    #         if self.object.action == Change.Actions.UPDATE
    #         else reverse("change-gcmd", args=[self.object.pk])
    #     )
    #     if self.request.GET.get("back"):
    #         return f'{url}?back={self.request.GET["back"]}'
    #     return url

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
            "ancestors": (context["object"].get_ancestors().select_related("content_type")),
            "descendents": (context["object"].get_descendents().select_related("content_type")),
        }
        print(f"Context Data: {context}")
        return context

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_affected_type(self):
        content_type = self.get_model_form_content_type().model_class().__name__
        if content_type == "GcmdPlatform":
            return "Platform"
        elif content_type == "GcmdProject":
            return "Campaign"
        elif content_type in ["GcmdInstrument", "GcmdPhenomena"]:
            return "Instrument"

    def get_affected_url(self, uuid):
        content_type = self.get_model_form_content_type().model_class().__name__
        back = f"?back=/drafts/edit/gcmd/{self.object.uuid}"
        if content_type == "GcmdPlatform":
            return f"/platforms/published/{uuid}/edit{back}"
        elif content_type == "GcmdProject":
            return f"/campaigns/published/{uuid}/edit{back}"
        elif content_type in ["GcmdInstrument", "GcmdPhenomena"]:
            return f"/instruments/published/{uuid}/edit{back}"

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

        def compare_gcmd_path_attribute(attribute, new_object, old_object=None):
            return {
                "key": attribute,
                "old_value": model_to_dict(old_object).get(attribute, '')
                if old_object is not None
                else '',
                "new_value": new_object.update.get(attribute, ''),
                "has_changed": old_object is None
                or new_object.update is {}
                or not model_to_dict(old_object)[attribute] == new_object.update[attribute],
            }

        content_type = self.get_model_form_content_type().model_class()
        print(f"GCMD PATH, Object: {vars(self.object)}")
        print(f"GCMD PATH, content type: {content_type}")
        path = {"new_path": True, "path": []}

        if content_type not in [GcmdPlatform, GcmdProject, GcmdInstrument, GcmdPhenomena]:
            return {}

        # TODO: Use non-hardcoded value for "Update", "Delete", "Create"
        if self.object.action in ["Update", "Delete"]:
            path["old_path"] = True
            # TODO: .get method should work for finding GCMD objects, but maybe add exception in case.
            gcmd_object = content_type.objects.get(uuid=self.object.model_instance_uuid)
        # The action is a Create so there isn't a gcmd_object or an old_path.
        else:
            path["old_path"] = False
            gcmd_object = None

        path_order = path_order[content_type.__name__]
        for attribute in path_order:
            path["path"].append(compare_gcmd_path_attribute(attribute, self.object, gcmd_object))
        print(f"Final Path: {path}")
        return path

    # TODO: Clean up this method:
    # * Take out imports & prints
    # * The Platform, Campaign, and Instrument queries are similair enough to combine into one.
    def get_affected_records(self) -> Dict:
        affected_records = []

        content_type = self.get_model_form_content_type().model_class().__name__
        if content_type == "GcmdPlatform":
            queryset = Platform.objects.filter(
                aliases__short_name=self.object.update["short_name"]
            ).exclude(gcmd_platforms__short_name=self.object.update["short_name"])
        elif content_type == "GcmdProject":
            queryset = Campaign.objects.filter(
                aliases__short_name=self.object.update["short_name"]
            ).exclude(gcmd_projects__short_name=self.object.update["short_name"])
        elif content_type == "GcmdInstrument":
            queryset = Instrument.objects.filter(
                aliases__short_name=self.object.update["short_name"]
            ).exclude(gcmd_instruments__short_name=self.object.update["short_name"])
        elif content_type == "GcmdPhenomena":
            queryset = Instrument.objects.filter(
                aliases__short_name=self.object.update["short_name"]
            ).exclude(gcmd_phenomenas__short_name=self.object.update["short_name"])
        else:
            return []
        print(f"Query Set: {queryset}")
        category = self.get_affected_type()
        for row in queryset:
            affected_records.append(
                {
                    "row": row,
                    "status": "Published",
                    "category": category,
                    "link": self.get_affected_url(row.uuid),
                }
            )

        print(f"Alias #1: {model_to_dict(queryset[0])}")
        return affected_records

    def get_model_form_intial(self):
        return self.object.update

    def get_back_button_url(self):
        """
        In the case where the back button returns the user to the table view for that model type, specify
        which table view the user should be redirected to.
        """
        content_type = self.get_model_form_content_type().model_class().__name__
        button_mapping = {
            "GcmdProject": "review_changes-list-draft",
            "GcmdInstrument": "review_changes-list-draft",
            "GcmdPlatform": "review_changes-list-draft",
            "GcmdPhenomena": "review_changes-list-draft",
        }
        return button_mapping.get(content_type, "summary")

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        return super().post(*args, **kwargs)
