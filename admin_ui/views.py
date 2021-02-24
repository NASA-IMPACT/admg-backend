from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import TextField, UUIDField
from django.db.models.expressions import F, Func, Value
from django.db.models.functions import Cast
from django.forms import ModelForm, Textarea, modelform_factory
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic.edit import UpdateView

import requests

from api_app.models import Change


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


class ChangeForm(ModelForm):
    class Meta:
        model = Change
        exclude = []
        widgets = {"notes": Textarea()}


class CampaignGroupView(UpdateView):
    template_name = "admin/change_group_detail.html"
    pk_url_kwarg = "uuid"

    @staticmethod
    def fetch_related_data(campaign_id):
        rel_deployments = Change.objects.filter(
            content_type__model__iexact="deployment", update__campaign=campaign_id
        )
        rel_collection_periods = Change.objects.filter(
            content_type__model__iexact="collectionperiod",
            update__deployment__in=[
                str(d.uuid) for d in rel_deployments
            ],  # TODO: Using a queryset for the lookup may be more performant
        )
        platform_ids = set()
        homebase_ids = set()
        instrument_ids = set()
        for collect_period in rel_collection_periods:
            update = collect_period.update
            platform_ids.add(update.get("platform"))
            homebase_ids.add(update.get("home_base"))
            instrument_ids.update(update.get("instruments"))

        rel_platforms = Change.objects.filter(
            content_type__model__iexact="platform", uuid__in=platform_ids
        )
        rel_homebases = Change.objects.filter(
            content_type__model__iexact="homebase", uuid__in=homebase_ids
        )
        rel_instruments = Change.objects.filter(
            content_type__model__iexact="instrument", uuid__in=instrument_ids
        )
        return {
            "deployments": rel_deployments,
            "collection_periods": rel_collection_periods,
            "platforms": rel_platforms,
            "homebases": rel_homebases,
            "deployments": rel_deployments,
            "instruments": rel_instruments,
        }

    @classmethod
    def build_dependencies(cls, campaign_change) -> None:
        """
        Given a campaign, inject related Changes to follow the following dependencies:
        - campaign
        - deployments
            - collection_periods
            - platforms
            - homebases
            - instruments
        """
        related = cls.fetch_related_data(str(campaign_change.uuid))
        campaign_change.deployments = [deployment for deployment in related["deployments"]]
        for deployment in campaign_change.deployments:
            deployment.collection_periods = [
                cp
                for cp in related["collection_periods"]
                if cp.update.get("deployment") == str(deployment.uuid)
            ]
            for collection_period in deployment.collection_periods:
                collection_period.platforms = [
                    p
                    for p in related["platforms"]
                    if str(p.uuid) == collection_period.update.get("platform")
                ]
                collection_period.homebases = [
                    hb
                    for hb in related["homebases"]
                    if str(hb.uuid) == collection_period.update.get("home_base")
                ]
                collection_period.instruments = [
                    i
                    for i in related["instruments"]
                    if str(i.uuid) in collection_period.update.get("instruments")
                ]

    def get_queryset(self):
        return Change.objects.filter(
            content_type__model__iexact="campaign",
            action="Create",  # Limit to only Create changes for now
        ).select_related('content_type')

    def get_form_class(self):
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/contrib/admin/options.py#L670-L711
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/forms/models.py#L483
        # return modelform_factory(self.object.__class__)
        return modelform_factory(self.object.content_type.model_class(), exclude=[])

    def get_initial(self):
        return self.object.update

    def get_context_data(self):
        self.build_dependencies(self.object)
        return {
            **super().get_context_data(),
            "change_form": ChangeForm(instance=self.object, prefix="change__"),
        }
