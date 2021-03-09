import django_tables2 as tables
from django_tables2 import A

from api_app.models import Change


class ChangeListTable(tables.Table):
    short_name = tables.LinkColumn(
        viewname="change-detail",
        args=[A("uuid")],
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="update__funding_agency"
    )
    updated_at = tables.Column(verbose_name="Last Edit Date")

    class Meta:
        attrs = {"class": "table table-striped", "thead": {"class": "thead-dark"}}
        model = Change
        fields = ["short_name", "long_name", "funding_agency", "status", "updated_at"]


class ChangeSummaryTable(tables.Table):
    name = tables.LinkColumn(
        viewname="change-detail",
        args=[A("uuid")],
        verbose_name="Name",
        accessor="update__short_name",
    )
    short_name = tables.Column(verbose_name="Campaign", accessor="update__short_name")
    content_type__model = tables.Column(
        verbose_name="Model Type", accessor="content_type__model"
    )
    updated_at = tables.Column(verbose_name="Last Edit Date")
    status = tables.Column(verbose_name="Status", accessor="status")

    class Meta:
        attrs = {"class": "table table-striped", "thead": {"class": "thead-dark"}}
        model = Change
        fields = ["name", "content_type__model", "updated_at", "short_name", "status"]
