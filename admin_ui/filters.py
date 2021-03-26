import django_filters

from api_app.models import Change


class ChangeStatusFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="iexact"
    )

    class Meta:
        model = Change
        fields = ["status"]
