import django_filters

from api_app.models import Change


class ChangeStatusFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="iexact"
    )
    # nasa_led = django_filters.BooleanFilter(
    #     label="NASA Led", field_name="update__nasa_led"
    # )
    # funding_agency = django_filters.Filter(
    #     label="Funding Agency", field_name="update__funding_agency"
    # )

    class Meta:
        model = Change
        fields = ["status"]
