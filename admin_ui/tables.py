import django_tables2 as tables
from django_tables2 import A

from api_app.models import Change


class CampaignChangeListTable(tables.Table):
    short_name = tables.Column(
        linkify=("change-detail", [A("uuid")]),
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="update__funding_agency"
    )

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "thead-dark"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "funding_agency", "status", "updated_at"]


class PlatformChangeListTable(tables.Table):
    short_name = tables.Column(
        linkify=("change-form", [A("uuid")]),
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    platform_type = tables.Column(
        verbose_name="Platform Type", accessor="platform_type_name"
    )

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "thead-dark"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "platform_type", "status", "updated_at"]


class BasicChangeListTable(tables.Table):
    short_name = tables.Column(
        linkify=("change-form", [A("uuid")]),
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "thead-dark"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "status", "updated_at"]


class MultiItemListTable(BasicChangeListTable):
    model_name = tables.Column(verbose_name="Item Type", accessor="content_type__model")

    class Meta:
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "thead-dark"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "model_name", "status", "updated_at"]


class ChangeSummaryTable(tables.Table):
    name = tables.LinkColumn(
        viewname="change-detail",
        args=[A("uuid")],
        verbose_name="Name",
        accessor="update__short_name",
    )
    content_type__model = tables.Column(
        verbose_name="Model Type", accessor="model_name", order_by="content_type__model"
    )
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    status = tables.Column(verbose_name="Status", accessor="status")

    class Meta:
        model = Change
        attrs = {"class": "table table-striped", "thead": {"class": "thead-dark"}}
        fields = ["name", "content_type__model", "updated_at", "status"]
