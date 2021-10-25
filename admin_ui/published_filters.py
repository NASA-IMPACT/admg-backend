import django_filters
from data_models import models


def GenericPublishedListFilter(model_name):

    class GenericFilterClass(django_filters.FilterSet):
        short_name = django_filters.CharFilter(
            label="Short Name", field_name="short_name", lookup_expr="icontains"
        )
        class Meta:
            model = getattr(models, model_name)
            fields = ["short_name"]

    return GenericFilterClass
