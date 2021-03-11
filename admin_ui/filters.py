import django_filters

from api_app.models import Change


class ChangeStatusFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Change
        fields = ["status"]
