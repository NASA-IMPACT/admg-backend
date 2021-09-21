from data_models.models import Campaign, Website
import django_tables2 as tables
from django_tables2 import A

from api_app.models import Change


class CustomTemplateColumn(tables.TemplateColumn):
    # change here accordingly
    def render(self, record, table, value, bound_column, **kwargs):
        if record.status != 6: # published
            return ''
        return super().render(record, table, value, bound_column, **kwargs)

class CustomTable(tables.Table):
    # change here accordingly
    type = tables.Column(verbose_name="Type of request", accessor="type")
    T1     = '<button type="button" class="btn">update</button>'
    T2     = '<button type="button" class="btn">delete</button>'
    edit   = CustomTemplateColumn(T1)
    delete = CustomTemplateColumn(T2)

class PublishedCampaignListTable(CustomTable):
    short_name = tables.Column(
        linkify=("mi-campaign-detail", [A("uuid")]),
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="update__funding_agency"
    )

    class Meta:
        model = Campaign
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "funding_agency", "updated_at"]

class CampaignChangeListTable(PublishedCampaignListTable):
    status = tables.Column(verbose_name="Status", accessor="status")
    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "funding_agency", "status", "updated_at"]


class PlatformChangeListTable(CustomTable):
    short_name = tables.Column(
        linkify=("mi-change-update", [A("uuid")]),
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
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "platform_type", "status", "updated_at"]


class BasicChangeListTable(CustomTable):
    short_name = tables.Column(
        linkify=("mi-change-update", [A("uuid")]),
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
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "status", "updated_at"]


class MultiItemListTable(BasicChangeListTable):
    model_name = tables.Column(verbose_name="Item Type", accessor="content_type__model")

    class Meta:
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "model_name", "status", "updated_at"]


class ChangeSummaryTable(CustomTable):
    name = tables.LinkColumn(
        viewname="mi-campaign-detail",
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
        attrs = {"class": "table table-striped", "thead": {"class": "table-primary"}}
        fields = ["name", "content_type__model", "updated_at", "status"]


class WebsiteChangeListTable(CustomTable):
    title = tables.Column(
        linkify=("mi-change-update", [A("uuid")]),
        verbose_name="Title", 
        accessor="update__title"
    )
    url = tables.Column(verbose_name="URL", accessor="update__url")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    website_type = tables.Column(
        verbose_name="Website Type", accessor="website_type_name"
    )

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["title", "url", "website_type", "status", "updated_at"]


class CampaignWebsiteChangeListTable(CustomTable):
    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }


class AliasChangeListTable(CustomTable):
    short_name = tables.Column(
        linkify=("mi-change-update", [A("uuid")]),
        verbose_name="Short Name", 
        accessor="update__short_name"
    )
    # TODO replace model_type which short_name of related object
    model_type = tables.Column(verbose_name="Item Type", accessor="update__model_name")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "model_type", "status", "updated_at"]
