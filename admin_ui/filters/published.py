import django_filters
from data_models import models
from data_models.models import DOI, Deployment, Image, Website

from .filters import CampaignFilter
from .utils import default_filter_configs, get_published_campaigns, get_deployments

# TODO: Look at .values with Cast function


def GenericPublishedListFilter(model_name, filter_configs=default_filter_configs):
    class GenericFilterClass(django_filters.FilterSet):
        class Meta:
            model = getattr(models, model_name)
            fields = []

    for config in filter_configs:
        GenericFilterClass.base_filters[config["field_name"]] = django_filters.CharFilter(
            label=config["label"], field_name=config["field_name"], lookup_expr="icontains"
        )

    return GenericFilterClass


class WebsiteFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label="Title", field_name="title", lookup_expr="icontains")
    url = django_filters.CharFilter(label="url", field_name="url", lookup_expr="icontains")

    class Meta:
        model = Website
        fields = ["title", "url"]


class DeploymentFilter(CampaignFilter):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="short_name", lookup_expr="icontains"
    )

    def filter_campaign_name(self, queryset, field_name, search_string):
        campaigns = get_published_campaigns(search_string)
        return queryset.filter(campaign__in=campaigns)

    class Meta:
        model = Deployment
        fields = ["short_name"]


def second_level_campaign_filter(model_name):

    Model = getattr(models, model_name)

    class FilterForDeploymentToCampaign(DeploymentFilter):
        def filter_campaign_name(self, queryset, field_name, search_string):
            campaigns = get_published_campaigns(search_string)
            deployments = get_deployments(campaigns)
            return queryset.filter(deployment__in=deployments)

        class Meta:
            model = Model
            fields = ["short_name"]

    return FilterForDeploymentToCampaign


class DoiFilter(CampaignFilter):
    concept_id = django_filters.CharFilter(
        label="Concept ID", field_name="concept_id", lookup_expr="icontains"
    )

    def filter_campaign_name(self, queryset, field_name, search_string):
        campaigns = get_published_campaigns(search_string)
        return queryset.filter(campaigns__in=campaigns)

    class Meta:
        model = DOI
        fields = ["concept_id"]


class CollectionPeriodFilter(CampaignFilter):
    def filter_campaign_name(self, queryset, field_name, search_string):
        campaigns = get_published_campaigns(search_string)
        deployments = get_deployments(campaigns)
        return queryset.filter(deployment__in=deployments)

    class Meta:
        model = DOI
        fields = ["campaign_name"]


class ImageFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label="Title", field_name="title", lookup_expr="icontains")

    class Meta:
        model = Image
        fields = ["title"]
