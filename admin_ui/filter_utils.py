import django_filters

from api_app.models import Change
from data_models import models
from data_models.models import Campaign, Deployment
from django.db.models.query_utils import Q


default_filter_configs = [{"field_name": "short_name", "label": "Short Name"}]


class CampaignFilter(django_filters.FilterSet):
    # make sure to include a filter_campaign_name method in the inherited classes
    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="",
        method="filter_campaign_name",
    )


def get_published_campaigns(search_string):
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


def get_draft_campaigns(search_string):
    """Takes a search_string  and finds all draft and published campaigns with a matching
    value in their short or long_name. Not case sensitive.

    Args:
        search_string (str): short/long_name or piece of a short/long_name.

    Returns:
        all_campaign_uuids: uuids for the matching campaigns
    """

    campaign_model_uuids = get_published_campaigns(search_string)

    campaign_draft_uuids = (
        Change.objects.of_type(Campaign)
        .filter(
            Q(update__short_name__icontains=search_string)
            | Q(update__long_name__icontains=search_string)
        )
        .values_list("uuid")
    )

    all_campaign_uuids = campaign_model_uuids.union(campaign_draft_uuids)

    return all_campaign_uuids


def get_deployments(campaign_uuids):
    deployments = Deployment.objects.filter(campaign__in=campaign_uuids).values_list("uuid")

    return deployments


def filter_draft_and_published(model_name):
    """Filtering the drafts work a bit differently as they need to look at their
    own values (inside update) and also look for models (for update/delete drafts)
    that they point to, in order to find the items in the draft table

    This function should be used in the "method" parameter in the django_filters field

    Args:
        model_name (str): the model which the draft belongs to

    Returns:
        filter_field_name (function): The function required by the "method" parameter
    """

    def filter_field_name(queryset, field_name, search_string):
        """method function for fields
        Args:
            queryset (django QuerySet): initial queryset obtained
            field_name (str): the field name this filter is being applied to
            search_string (str): the string that needs to be searched for

        Returns:
            queryset (django QuerySet):

        """

        field_name_in_draft_query = {f"{field_name}__icontains": search_string}

        # remove the "update__" part for the field_name
        model_field_name = field_name.replace("update__", "")
        Model = getattr(models, model_name)
        matching_model_instances = Model.objects.filter(
            **{f"{model_field_name}__icontains": search_string}
        ).values_list("uuid")

        return queryset.filter(
            Q(**field_name_in_draft_query) | Q(model_instance_uuid__in=matching_model_instances)
        )

    return filter_field_name


def second_level_campaign_name_filter(queryset, search_string, model):
    """Returns campaigns for those models which link to campaign like model -> deployment -> campaign

    Args:
        queryset (Django QuerySet): original queryset
        search_str (str): string to search for
        model (Django Model instance): the model that is being queried

    Returns:
        queryset (Django QuerySet): queryset after the filters have been applied
    """

    campaigns = get_draft_campaigns(search_string)
    deployments = get_deployments(campaigns)
    deployments_change_objects = Change.objects.of_type(Deployment).filter(
        Q(model_instance_uuid__in=deployments)
        | Q(update__campaign__in=(str(val[0]) for val in campaigns))
    )

    model_instances = model.objects.filter(deployment__in=deployments)
    unioned_deployments = deployments.union(deployments_change_objects.values_list("uuid"))
    return queryset.filter(
        Q(model_instance_uuid__in=model_instances)
        | Q(update__deployment__in=(str(val[0]) for val in unioned_deployments))
    )
