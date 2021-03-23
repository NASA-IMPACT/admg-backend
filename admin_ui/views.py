from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.db.models import functions, expressions, aggregates, Max
from django.db.models.fields.json import KeyTextTransform
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import DetailView
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    View,
    FormMixin,
    ProcessFormView,
)
import django_tables2
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
from data_models.models import Campaign, Instrument, Platform, PlatformType, PartnerOrg
from . import tables, forms, mixins


@login_required
@user_passes_test(lambda user: user.can_deploy())
def deploy_admin(request):
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

    # TODO: Redirect back to origin of request
    # TODO: Use dynamic admin route (either from URL router or from settings)
    return HttpResponseRedirect("/admin/")


@method_decorator(login_required, name="dispatch")
class ChangeSummaryView(django_tables2.SingleTableView):
    model = Change
    model_names = [
        M._meta.model_name for M in (Campaign, Platform, Instrument, PartnerOrg)
    ]
    table_class = tables.ChangeSummaryTable
    paginate_by = 10
    template_name = "api_app/summary.html"

    def get_queryset(self):
        return (
            Change.objects.filter(
                content_type__model__in=self.model_names, action=CREATE
            )
            # Prefetch related ContentType (used when displaying output model type)
            .select_related("content_type")
            # Add last related ApprovalLog's date
            .annotate(updated_at=aggregates.Max("approvallog__date")).order_by(
                "-updated_at"
            )
        )

    def get_draft_status_count(self):
        status_ids = [IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE, PUBLISHED_CODE]
        status_translations = {
            status_id: status_name.replace(" ", "_")
            for status_id, status_name in AVAILABLE_STATUSES
        }

        # Setup dict with 0 counts
        review_counts = {
            model: {
                status.replace(" ", "_"): 0 for status in status_translations.values()
            }
            for model in self.model_names
        }

        # Populate with actual counts
        model_status_counts = (
            Change.objects.filter(
                action=CREATE,
                content_type__model__in=self.model_names,
                status__in=status_ids,
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
            "total_counts": {"campaign": None, "platform": None, "instrument": None},
            "draft_status_counts": self.get_draft_status_count(),
            "activity_list": ApprovalLog.objects.prefetch_related(
                "change__content_type", "user"
            ).order_by("-date")[:self.paginate_by / 2],
        }


@method_decorator(login_required, name="dispatch")
class ChangeListView(django_tables2.SingleTableView):
    model = Change
    table_class = tables.CampaignChangeListTable
    template_name = "api_app/change_list.html"

    def get_queryset(self):
        return (
            Change.objects.filter(content_type__model="campaign", action=CREATE)
            # Add last related ApprovalLog's date
            .annotate(updated_at=aggregates.Max("approvallog__date"))
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Campaign",
            "model": "campaign",
        }


@method_decorator(login_required, name="dispatch")
class ChangeDetailView(SingleObjectMixin, ListView):
    model = Change
    paginate_by = 25
    template_name = "api_app/change_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Change.objects.all())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Change.objects.filter(
                content_type__model="deployment",
                update__campaign=str(self.kwargs[self.pk_url_kwarg]),
            )
            .prefetch_related(
                models.Prefetch(
                    "approvallog_set",
                    queryset=ApprovalLog.objects.order_by("-date").select_related(
                        "user"
                    ),
                    to_attr="approvals",
                )
            )
            .order_by(self.get_ordering())
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "significant_events": (
                Change.objects.select_related("content_type")
                .filter(
                    content_type__model__iexact="significantevent",
                    update__deployment__in=[str(d.uuid) for d in self.object_list],
                )
                .prefetch_related(
                    models.Prefetch(
                        "approvallog_set",
                        queryset=ApprovalLog.objects.order_by("-date").select_related(
                            "user"
                        ),
                        to_attr="approvals",
                    )
                )
                # Add related IOP's short_name if it exists
                .annotate(
                    iop_uuid=functions.Cast(
                        KeyTextTransform("iop", "update"), models.UUIDField()
                    ),
                    iop_name=expressions.Subquery(
                        Change.objects.filter(
                            content_type__model__iexact="iop",
                            action=CREATE,
                            uuid=expressions.OuterRef("iop_uuid"),
                        ).values("update__short_name")[:1]
                    ),
                )
            ),
            "iops": (
                Change.objects.select_related("content_type")
                .filter(
                    content_type__model__iexact="iop",
                    update__deployment__in=[str(d.uuid) for d in self.object_list],
                )
                .prefetch_related(
                    models.Prefetch(
                        "approvallog_set",
                        queryset=ApprovalLog.objects.order_by("-date").select_related(
                            "user"
                        ),
                    )
                )
            ),
            "collection_periods": (
                Change.objects.select_related("content_type")
                .filter(
                    content_type__model__iexact="collectionperiod",
                    update__deployment__in=[str(d.uuid) for d in self.object_list],
                )
                .prefetch_related(
                    models.Prefetch(
                        "approvallog_set",
                        queryset=ApprovalLog.objects.order_by("-date").select_related(
                            "user"
                        ),
                        to_attr="approvals",
                    )
                )
                # Add related Platform's short_name
                .annotate(
                    platform_uuid=functions.Cast(
                        KeyTextTransform("platform", "update"), models.UUIDField()
                    ),
                    platform_name=expressions.Subquery(
                        Change.objects.filter(
                            content_type__model=Platform._meta.model_name,

                            uuid=expressions.OuterRef("platform_uuid")
                        ).values("short_name")[:1]
                    ),
                )
                # Add related Instrument's short_name
                .annotate(
                    instrument_uuid=functions.Cast(
                        KeyTextTransform("instrument", "update"), models.UUIDField()
                    ),
                    instrument_name=expressions.Subquery(
                        Change.objects.filter(
                            content_type__model=Instrument._meta.model_name,

                            uuid=expressions.OuterRef("instrument_uuid")
                        ).values("short_name")[:1]
                    ),
                )
            ),
        }

    def get_ordering(self):
        return self.request.GET.get("ordering", "-status")


@method_decorator(login_required, name="dispatch")
class ChangeCreateView(mixins.ChangeModelFormMixin, CreateView):

    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/change_add_form.html"

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
            "content_type_name": self.get_model_form_content_type()
            .model_class()
            .__name__,
        }

    def get_success_url(self):
        return reverse("change-form", args=[self.object.pk])

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
    success_url = "/"
    fields = ["content_type", "model_instance_uuid", "action", "update", "status"]

    prefix = "change"
    template_name = "api_app/change_form.html"

    def get_queryset(self):
        # Prefetch content type for performance
        return Change.objects.select_related("content_type")

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "transition_form": forms.TransitionForm(
                change=self.get_object(), user=self.request.user
            ),
            # Add approvals to context
            "approvals": self.get_object()
            .approvallog_set.order_by("-date")
            .prefetch_related("user"),
        }

    def get_model_form_content_type(self) -> ContentType:
        return self.object.content_type

    def get_model_form_intial(self):
        return self.object.update

    def post(self, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        return super().post(*args, **kwargs)


@method_decorator(login_required, name="dispatch")
class PlatformListView(django_tables2.SingleTableView):
    model = Change
    table_class = tables.PlatformChangeListTable
    template_name = "api_app/change_list.html"

    def get_queryset(self):
        return (
            Change.objects.filter(content_type__model="platform", action=CREATE)
            # Add last related ApprovalLog's date
            .annotate(updated_at=aggregates.Max("approvallog__date"))
            # Add related PlatformType's short_name
            .annotate(
                platform_type_uuid=functions.Cast(
                    KeyTextTransform("platform_type", "update"), models.UUIDField()
                ),
                platform_type_name=expressions.Subquery(
                    Change.objects.filter(
                        content_type__model=PlatformType._meta.model_name,
                        action=CREATE,
                        uuid=expressions.OuterRef("platform_type_uuid")
                    ).values("short_name")[:1]
                ),
            )
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Platform",
            "model": "platform",
        }


@method_decorator(login_required, name="dispatch")
class InstrumentListView(django_tables2.SingleTableView):
    model = Change
    table_class = tables.BasicChangeListTable
    template_name = "api_app/change_list.html"

    def get_queryset(self):
        return Change.objects.filter(
            content_type__model="instrument", action=CREATE
        ).annotate(updated_at=Max("approvallog__date"))

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Instrument",
            "model": "instrument",
        }


@method_decorator(login_required, name="dispatch")
class PartnerOrgListView(django_tables2.SingleTableView):
    model = Change
    table_class = tables.BasicChangeListTable
    template_name = "api_app/change_list.html"

    def get_queryset(self):
        return Change.objects.filter(
            content_type__model=PartnerOrg._meta.model_name, action=CREATE
        ).annotate(updated_at=Max("approvallog__date"))

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "display_name": "Partner Organization",
            "model": PartnerOrg._meta.model_name,
        }


@login_required
def to_be_developed(request):
    return render(request, "api_app/to_be_developed.html")


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
