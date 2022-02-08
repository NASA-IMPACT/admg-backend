import django_filters
from api_app.models import Change
from data_models import models
from data_models.models import DOI, CollectionPeriod
from django.db.models.query_utils import Q

from .filter_utils import (
    CampaignFilter,
    default_filter_configs,
    get_draft_campaigns,
    get_deployments,
    filter_draft_and_published,
    second_level_campaign_name_filter,
)


# TODO:
# 1. Look at .values with Cast function
#   -> This is for queries like these: Q(update__campaigns__contains=(str(val[0]) for val in campaigns)
# 2. Merge the filters.py and published_filters.py into as single file.


def GenericDraftFilter(model_name, filter_configs=default_filter_configs):
    class GenericFilterClass(django_filters.FilterSet):
        class Meta:
            model = Change
            fields = [
                "status",
            ]

    for config in filter_configs:
        GenericFilterClass.base_filters[
            config["field_name"]
        ] = django_filters.CharFilter(
            label=config["label"],
            field_name=f"update__{config['field_name']}",
            method=filter_draft_and_published(
                model_name
            ),  # this is not required for published items
        )

    return GenericFilterClass


class WebsiteFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        label="Title",
        field_name="update__title",
        method=filter_draft_and_published("Website"),
    )
    url = django_filters.CharFilter(
        label="url",
        field_name="update__url",
        method=filter_draft_and_published("Website"),
    )


class DeploymentFilter(CampaignFilter):
    short_name = django_filters.CharFilter(
        label="Short Name",
        field_name="update__short_name",
        method=filter_draft_and_published("Deployment"),
    )

    def filter_campaign_name(self, queryset, field_name, search_string):

        campaigns = get_draft_campaigns(search_string)
        deployments = get_deployments(campaigns)
        return queryset.filter(
            Q(model_instance_uuid__in=deployments)
            | Q(update__campaign__in=(str(val[0]) for val in campaigns))
        )

    class Meta:
        model = Change
        fields = ["status"]


def second_level_campaign_filter(model_name):
    class FilterForDeploymentToCampaign(CampaignFilter):
        short_name = django_filters.CharFilter(
            label="Short Name",
            field_name="update__short_name",
            method=filter_draft_and_published(model_name),
        )

        def filter_campaign_name(self, queryset, field_name, search_string):

            # find instances that use deployment in the actual database instance
            model = getattr(models, model_name)
            return second_level_campaign_name_filter(queryset, search_string, model)

        class Meta:
            model = Change
            fields = ["status"]

    return FilterForDeploymentToCampaign


class DoiFilter(CampaignFilter):
    concept_id = django_filters.CharFilter(
        label="Concept ID",
        field_name="update__concept_id",
        lookup_expr=filter_draft_and_published("DOI"),
    )

    def filter_campaign_name(self, queryset, field_name, search_string):

        campaigns = get_draft_campaigns(search_string)
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


class CollectionPeriodFilter(CampaignFilter):
    def filter_campaign_name(self, queryset, field_name, search_string):

        return second_level_campaign_name_filter(
            queryset, search_string, CollectionPeriod
        )

    class Meta:
        model = Change
        fields = ["status"]
