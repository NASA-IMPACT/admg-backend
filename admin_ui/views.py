import json
from typing import Union
import django_tables2 as tables
from django_tables2 import SingleTableView, A

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.db.models.aggregates import Count, Max
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin
from django.db.models import Max
from django.db.models.query import QuerySet
from rest_framework.renderers import JSONRenderer
import requests

from api_app.models import ApprovalLog, Change, CREATE, UPDATE, PUBLISHED_CODE
from data_models.models import Campaign, Instrument, Platform, Deployment


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


class ChangeModelFormMixin(ModelFormMixin):
    """
    This mixin attempts to simplify working with a second form (the model_form)
    when editing Change objects.
    """

    destination_model_prefix = "model_form"

    @property
    def destination_model_form(self):
        """ Helper to return a form for the destination of the Draft object """
        return modelform_factory(
            self.get_model_form_content_type().model_class(), exclude=[]
        )

    def get_model_form_content_type(self) -> ContentType:
        raise NotImplementedError("Subclass must implement this property")

    def get_model_form_intial(self):
        return {}

    def get_context_data(self, **kwargs):
        if "model_form" not in kwargs:
            # Ensure that the model_form is available in context for template
            kwargs["model_form"] = self.destination_model_form(
                initial=self.get_model_form_intial(),
                prefix=self.destination_model_prefix,
            )
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        # Validate destination model's form
        BaseModelForm = self.destination_model_form

        class ModelForm(BaseModelForm):
            # TODO: This may be a mistake, I don't know if we ever want to actually ignore validation errors.
            # Instead, we still may want to save the form but also render the validation errors.
            def validate_unique(_self):
                # We don't want to raise errors on unique errors for the
                # destination model unless this is a "Create" change
                if self.object.action == CREATE:
                    super().validate_unique()

        model_form = ModelForm(data=request.POST, prefix=self.destination_model_prefix)
        form = self.get_form()

        if not all([model_form.is_valid(), form.is_valid()]):
            return self.form_invalid(form=form, model_form=model_form)

        # Populate Change's form with values from destination model's form
        form.instance.update = json.loads(
            JSONRenderer().render(
                {k: serialize(v) for k, v in model_form.cleaned_data.items()}
            )
        )
        return self.form_valid(form)

    def form_invalid(self, form, model_form):
        # Overriden to support handling both invalid Change form and an invalid
        # destination model form
        return self.render_to_response(
            self.get_context_data(form=form, model_form=model_form)
        )


class SummaryTable(tables.Table):
    name = tables.LinkColumn(
        viewname="change-detail",
        args=[A("uuid")],
        verbose_name="Name",
        accessor="update__short_name",
    )
    short_name = tables.Column(
        verbose_name="Campaign",
        accessor="update__short_name",
    )
    content_type__model = tables.Column(
        verbose_name="Model Type", accessor="content_type__model"
    )
    updated_at = tables.Column(verbose_name="Last Edit Date")
    status = tables.Column(verbose_name="Status", accessor="status")

    class Meta:
        attrs = {"class": "table table-striped", "thead": {"class": "thead-dark"}}
        model = Change
        fields = ["name", "content_type__model", "updated_at", "short_name", "status"]


class ChangeSummaryView(SingleTableView):
    model = Change
    table_class = SummaryTable
    paginate_by = 25
    template_name = "api_app/summary.html"

    def get_queryset(self):
        return (
            Change.objects.filter(content_type__model="campaign", action=CREATE)
            .annotate(updated_at=Max("approvallog__date"))
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "change_counts": {
                k: v
                for (k, v) in Change.objects.filter(
                    action=CREATE,
                    content_type__model__in=[
                        "campaign",
                        "deployment",
                        "instrument",
                        "platform",
                    ],
                )
                .exclude(status=PUBLISHED_CODE)
                .values_list("content_type__model")
                .annotate(total=Count("content_type"))
            },
            "published_counts": {
                Model.__name__.lower(): Model.objects.count()
                for Model in [Campaign, Deployment, Instrument, Platform]
            },
            "activity_list": ApprovalLog.objects.prefetch_related(
                "change__content_type"
            ).order_by("-date")[: self.paginate_by],
        }


class ChangeTable(tables.Table):
    short_name = tables.LinkColumn(
        viewname="change-detail",
        args=[A("uuid")],
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="update__funding_agency"
    )
    updated_at = tables.Column(verbose_name="Last Edit Date")

    class Meta:
        attrs = {"class": "table table-striped", "thead": {"class": "thead-dark"}}
        model = Change
        fields = ["short_name", "long_name", "funding_agency", "status", "updated_at"]


class ChangeListView(SingleTableView):
    model = Change
    table_class = ChangeTable
    template_name = "api_app/change_list.html"

    def get_queryset(self):
        return Change.objects.filter(
            content_type__model="campaign", action=CREATE
        ).annotate(updated_at=Max("approvallog__date"))



class ChangeDetailView(DetailView):
    model = Change
    template_name = "api_app/change_detail.html"


class ChangeCreateView(CreateView, ChangeModelFormMixin):
    model = Change
    fields = ["content_type", "model_instance_uuid", "action", "update"]
    template_name = "api_app/change_add_form.html"

    def get_initial(self):
        # Get initial form values from URL
        return {
            "content_type": self.get_model_form_content_type().id,
            "action": UPDATE if self.request.GET.get("uuid") else CREATE,
            "model_instance_uuid": self.request.GET.get("uuid"),
        }

    def get_model_form_content_type(self) -> ContentType:
        return ContentType.objects.get(
            app_label="data_models", model__iexact=self.kwargs["model"]
        )

    def get_model_form_intial(self):
        # TODO: Not currently possible to handle reverse relationships such as adding
        # models to a CollectionPeriod where the FK is on the Collection Period
        return {k: v for k, v in self.request.GET.dict().items() if k != "uuid"}


class ChangeUpdateView(UpdateView, ChangeModelFormMixin):
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
            # Add approvals to context
            "approvals": self.get_object().approvallog_set.order_by("-date"),
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


def serialize(value):
    if isinstance(value, QuerySet):
        return [v.uuid for v in value]
    if isinstance(value, models.Model):
        return value.uuid
    return value
