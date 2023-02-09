from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from api_app.models import Change
from data_models import models
from .. import filters, forms, mixins, tables, utils


@method_decorator(login_required, name="dispatch")
class CanonicalRecordList(mixins.DynamicModelMixin, SingleTableMixin, FilterView):
    model = Change
    template_name = "api_app/change_list.html"

    def get_table_class(self):
        return self._model_config["change_list_table"]

    def get_filterset_class(self):
        return self._model_config["draft_filter"]

    def get_queryset(self):
        queryset = (
            Change.objects.filter(action=Change.Actions.CREATE)
            .of_type(self._model_config['model'])
            .order_by("-updated_at")
        )

        if self._model_config['model'] == models.Platform:
            return queryset.annotate_from_relationship(
                of_type=models.PlatformType, uuid_from="platform_type", to_attr="platform_type_name"
            )
        else:
            return queryset

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "url_name": self._model_config["singular_snake_case"],
            "view_model": self._model_name,
            "display_name": self._model_config["display_name"],
        }


@method_decorator(login_required, name="dispatch")
class CanonicalRecordPublished(DetailView):
    template_name = "api_app/canonical/published_detail.html"
    pk_url_kwarg = 'canonical_uuid'

    def get_queryset(self):
        c = Change.objects.get(uuid=self.kwargs[self.pk_url_kwarg])
        Model = c.content_type.model_class()
        return Model.objects.all()
