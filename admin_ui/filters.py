import django_filters

from api_app.models import Change

from data_models.models import GcmdInstrument


class ChangeStatusFilter(django_filters.FilterSet):
    short_name = django_filters.CharFilter(
        label="Short Name", field_name="update__short_name", lookup_expr="icontains"
    )

    class Meta:
        model = Change
        fields = ["status"]


class MultiItemFilter(ChangeStatusFilter):
    # TODO why is this showing so many options?  Our queryset should be filtered
    content_type__model = django_filters.AllValuesFilter(label="Item Type")

    class Meta:
        model = Change
        fields = ["status"]
