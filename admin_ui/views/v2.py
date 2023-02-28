from typing import Dict

from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.views.generic.edit import UpdateView

from api_app.models import Change
from data_models.models import (
    IOP,
    Alias,
    Image,
    Platform,
    PlatformType,
    Website,
)
from .. import forms, mixins, utils
from api_app.views.generic_views import NotificationSidebar
from api_app.urls import camel_to_snake


# TODO add login requirement
def redirect_helper(request, canonical_uuid, model):
    try:
        draft = Change.objects.get(uuid=canonical_uuid)
        if draft.status == Change.Statuses.PUBLISHED:
            return redirect(reverse("canonical-published-detail", args=(canonical_uuid,)))
        # TODO return redirect to edit view
        # return HttpResponse("Todo return redirect")
        return redirect(reverse("canonical-draft-edit", args=(canonical_uuid,)))
    except Change.DoesNotExist:
        raise Http404("Canonial UI does not exist")


# Lists all the canonical records for a given model type
@method_decorator(login_required, name="dispatch")
class CanonicalRecordList(mixins.DynamicModelMixin, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"

    def get_table_class(self):
        return self._model_config["change_list_table"]

    def get_filterset_class(self):
        return self._model_config["draft_filter"]

    def get_queryset(self):
        queryset = (
            Change.objects.filter(action=Change.Actions.CREATE)
            .of_type(self._model_config['model'])
            .select_related("content_type")
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
class CanonicalRecordPublished(DetailView):
    template_name = "api_app/canonical/published_detail.html"
    pk_url_kwarg = 'canonical_uuid'

    def get_queryset(self):
        c = Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg])
        Model = c.content_type.model_class()
        return Model.objects.all()


@method_decorator(login_required, name="dispatch")
class CanonicalDraftEdit(NotificationSidebar, mixins.ChangeModelFormMixin, UpdateView):
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

    # TODO: FIX missing object pk (passing in canonical uuid from parent but not getting pk yet)
    def get_object(self, queryset=None
    ):
        change = Change.objects.select_related(
            "model_instance_uuid","content_type"
        )
        print(dir(change),"\n")
        print(change)
        if change.model_instance_uuid:
            return {'model_instance_uuid':change.model_instance_uuid,'content_type':change.content_type}

        else:
            HttpResponseBadRequest("Unable to find the document")

    # TODO: Find most recent draft for a given canonical_uuid
    # def get_object(self, queryset=None):
    # if canonical record is not published
    # if canonical record is published:
    # then return draft that is not published and the model_instance_uuid equals canonical_uuid
    # ...

    def get_success_url(self):
        url = reverse("change-update", args=[self.object.pk])
        if self.request.GET.get("back"):
            return f'{url}?back={self.request.GET["back"]}'
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            "object_pk": self.get_object()['model_instance_uuid'],
            "content_type": self.get_object()['content_type'],
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
