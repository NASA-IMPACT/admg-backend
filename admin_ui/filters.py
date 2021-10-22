import django_filters
from api_app.models import Change
from data_models import models
from data_models.models import DOI, Campaign, Deployment
from django.db.models.query_utils import Q

# TODO: Look at .values with Cast function


def _get_campaigns(short_name_segment):
    """Takes a short_name or piece of a short_name and finds all draft and
    published campaigns with a matching value. Not case sensitive.

    Args:
        short_name_segment (str): short_name or piece of a short_name.

    Returns:
        all_campaign_uuids: uuids for the matching campaigns
    """

    campaign_model_uuids = Campaign.objects.filter(
        short_name__icontains=short_name_segment
    ).values_list("uuid")

    campaign_draft_uuids = (
        Change.objects.of_type(Campaign)
        .filter(update__short_name__icontains=short_name_segment)
        .values_list("uuid")
    )

    all_campaign_uuids = campaign_model_uuids.union(campaign_draft_uuids)

    return all_campaign_uuids


def _get_deployments(campaign_uuids):
    deployments = Deployment.objects.filter(campaign__in=campaign_uuids).values_list(
        "uuid"
    )

    return deployments


class ChangeStatusFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="icontains"
    )

    # TODO: filter should show update drafts for those short names that it links to
    # def filter_short_name(self, queryset, name, value):
    #     pass

    class Meta:
        model = Change
        fields = ["status"]


class DeploymentFilter(ChangeStatusFilter):
    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="update__campaign",
        method="filter_campaign_name",
    )

    def filter_campaign_name(self, queryset, name, value):
        # limit search to 3 len or greater
        if not value or len(value) < 3:
            return queryset

        campaigns = _get_campaigns(value)
        deployments = _get_deployments(campaigns)
        return queryset.filter(
            Q(model_instance_uuid__in=deployments)
            | Q(update__campaign__in=(str(val[0]) for val in campaigns))
        )

    class Meta:
        model = Change
        fields = ["status"]


def second_level_campaign_filter(model_name):
    class FilterForDeploymentToCampaign(ChangeStatusFilter):
        campaign_name = django_filters.CharFilter(
            label="Campaign Name",
            field_name="update__campaign",
            method="filter_campaign_name",
        )

        def filter_campaign_name(self, queryset, name, value):
            # limit search to 3 len or greater
            if not value or len(value) < 3:
                return queryset

            campaigns = _get_campaigns(value)
            deployments = _get_deployments(campaigns)
            deployments_change_objects = Change.objects.of_type(Deployment).filter(
                Q(model_instance_uuid__in=deployments)
                | Q(update__campaign__in=(str(val[0]) for val in campaigns))
            )

            # find instances that use deployment in the actual database instance
            model = getattr(models, model_name)
            model_instances = model.objects.filter(deployment__in=deployments)

            unioned_deployments = deployments.union(
                deployments_change_objects.values_list("uuid")
            )
            return queryset.filter(
                Q(model_instance_uuid__in=model_instances)
                | Q(update__deployment__in=(str(val[0]) for val in unioned_deployments))
            )

    return FilterForDeploymentToCampaign


class DoiFilter(django_filters.FilterSet):
    concept_id = django_filters.CharFilter(
        label="Concept ID", field_name="update__concept_id", lookup_expr="icontains"
    )

    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="update__campaign",
        method="filter_campaign_name",
    )

    # TODO: filter should show update drafts for those short names that it links to
    # def filter_concept_id(self, queryset, name, value):
    #     pass

    def filter_campaign_name(self, queryset, name, value):
        # limit search to 3 len or greater
        if not value or len(value) < 3:
            return queryset

        campaigns = _get_campaigns(value)
        model_instances = DOI.objects.filter(campaigns__in=campaigns).values_list(
            "uuid"
        )
        return queryset.filter(
            Q(model_instance_uuid__in=model_instances)
            | Q(update__campaigns__contains=(str(val[0]) for val in campaigns))
        )

    class Meta:
        model = Change
        fields = ["status"]
