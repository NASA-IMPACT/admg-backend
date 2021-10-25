


import django_filters
from data_models import models
from data_models.models import DOI, Campaign, Deployment
from django.db.models.query_utils import Q
from .filters import get_deployments
# TODO: Look at .values with Cast function

def _get_campaigns(search_string):
    """Takes a search_string  and finds all published campaigns with a matching
    value in their short or long_name. Not case sensitive.

    Args:
        search_string (str): short/long_name or piece of a short/long_name.

    Returns:
        all_campaign_uuids: uuids for the matching campaigns
    """

    campaign_model_uuids = Campaign.objects.filter(
        Q(short_name__icontains=search_string) | Q(long_name__icontains=search_string)
    ).values_list("uuid")

    return campaign_model_uuids


default_filter_configs = [
    {
        "field_name": "short_name",
        "label": "Short Name" 
    }
]


def GenericPublishedListFilter(model_name, filter_configs=default_filter_configs):
    class GenericFilterClass(django_filters.FilterSet):
        class Meta:
            model = getattr(models, model_name)
            fields = ("uuid",)
    
    for config in filter_configs:
        GenericFilterClass.base_filters[config["field_name"]] = django_filters.CharFilter(
            label=config["label"], field_name=config["field_name"], lookup_expr="icontains"
        )

    return GenericFilterClass


class DeploymentFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name",
        field_name="short_name",
        lookup_expr="icontains",
    )
    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="campaign",
        method="filter_campaign_name",
    )

    def filter_campaign_name(self, queryset, field_name, search_string):
        campaigns = _get_campaigns(search_string)
        deployments = get_deployments(campaigns)
        return queryset.filter(uuid__in=deployments)

    class Meta:
        model = Deployment
        fields = ["short_name"]


def second_level_campaign_filter(model_name):
    
    Model = getattr(models, model_name)
    class FilterForDeploymentToCampaign(DeploymentFilter):

        def filter_campaign_name(self, queryset, field_name, search_string):
            campaigns = _get_campaigns(search_string)
            deployments = get_deployments(campaigns)
            return queryset.filter(deployment__in=deployments)
        
        class Meta:
            model = Model
            fields = ["short_name"]

    return FilterForDeploymentToCampaign


class DoiFilter(django_filters.FilterSet):
    concept_id = django_filters.CharFilter(
        label="Concept ID", field_name="concept_id", lookup_expr="icontains"
    )

    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="campaign",
        method="filter_campaign_name",
    )

    def filter_campaign_name(self, queryset, field_name, search_string):
        campaigns = _get_campaigns(search_string)
        return queryset.filter(campaigns__in=campaigns)

    class Meta:
        model = DOI
        fields = ["concept_id"]


