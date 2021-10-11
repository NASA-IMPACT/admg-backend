import django_filters

from api_app.models import Change
from data_models.models import Campaign


class ChangeStatusFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="icontains"
    )

    class Meta:
        model = Change
        fields = ["status"]


class DeploymentFilter(django_filters.FilterSet):
    campaign_name = django_filters.CharFilter(
        label="Campaign Name",
        field_name="update__campaign",
        method='filter_campaign_name'
    )
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="icontains"
    )

    def filter_campaign_name(self, queryset, name, value):
        if not value:
            return queryset

        uuid_set_model = Campaign.objects.filter(short_name__icontains=value).values_list("uuid")
        uuid_set_drafts = Change.objects\
            .filter(content_type__model="Campaign")\
            .filter(update__short_name__icontains=value)\
            .values_list("uuid")

        # all the uuids that have the name in the short name
        unioned_uuid = uuid_set_model.union(uuid_set_drafts)
        return queryset.filter(uuid__in=unioned_uuid)

    class Meta:
        model = Change
        fields = ["status"]
