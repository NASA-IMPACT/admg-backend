from data_models.models import Campaign, Website
import django_tables2 as tables
from django_tables2 import A
from django.urls import reverse


from api_app.models import Change, UPDATE, CREATE


class DraftLinkColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        self.published_viewname = kwargs.pop("published_viewname")
        self.viewname = kwargs.pop("viewname")
        self.url_kwargs = kwargs.pop("url_kwargs")

        return super().__init__(*args, **kwargs)

    def get_url(self, *args, **kwargs):
        record = kwargs.get("record")
        url_kwargs = {}
        for item in self.url_kwargs:
            url_kwargs[item] = getattr(record, self.url_kwargs[item])

        if record.action == UPDATE:
            return reverse(self.published_viewname, kwargs=url_kwargs)
        return reverse(self.viewname, kwargs=url_kwargs)


class DraftTableBase(tables.Table):
    draft_action = tables.Column(verbose_name="Draft Action", accessor="action")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")


class CampaignChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        published_viewname="campaign-diff-published",
        viewname="campaign-detail",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name"
    )
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="update__funding_agency"
    )

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "funding_agency", "draft_action", "status", "updated_at"]
        sequence = (
            "short_name",
            "long_name",
            "funding_agency",
            "draft_action",
            "status",
            "updated_at"
        )

# TODO: add sequences for all of the tables
class PlatformChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="Short Name",
        accessor="update__short_name",
    )
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
    status = tables.Column(verbose_name="Status", accessor="status")
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


class BasicChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
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


class ChangeSummaryTable(DraftTableBase):
    name = tables.LinkColumn(
        viewname="campaign-detail",
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


class WebsiteChangeListTable(DraftTableBase):
    title = tables.Column(
        linkify=("change-update", [A("uuid")]),
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


class CampaignWebsiteChangeListTable(DraftTableBase):
    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }


class AliasChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
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


class GcmdProjectChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="Short Name", 
        accessor="update__short_name"
    )
    long_name = tables.Column(verbose_name="Long Name", accessor="update__long_name")
    bucket = tables.Column(
        verbose_name="Bucket", accessor="update__bucket"
    )
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["title", "long_name", "status", "updated_at", "bucket",]


class GcmdInstrumentChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="short_name",
        accessor="update__short_name",
    )
    long_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="long_name",
        accessor="update__long_name",
    )
    instrument_category = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="instrument_category",
        accessor="update__instrument_category",
    )
    instrument_class = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="instrument_class",
        accessor="update__instrument_class",
    )
    instrument_type = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="instrument_type",
        accessor="update__instrument_type",
    )
    instrument_subtype = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="instrument_subtype",
        accessor="update__instrument_subtype",
    )
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="Short Name", 
        accessor="update__short_name"
    )
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = [
            "short_name",
            "long_name",
            "instrument_category",
            "instrument_class",
            "instrument_type",
            "instrument_subtype",
            "status",
            "updated_at",
        ]


class GcmdPlatformChangeListTable(DraftTableBase):
    short_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="short_name", 
        accessor="update__short_name"
    )
    long_name = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="long_name", 
        accessor="update__long_name"
    )
    category = tables.Column(
        linkify=("change-update", [A("uuid")]),
        verbose_name="category", 
        accessor="update__category"
    )
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["title", "long_name", "category", "status", "updated_at"]


class GcmdPhenomenaChangeListTable(DraftTableBase):
    category = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="category", 
            accessor="update__category"
        )
    topic = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="topic", 
            accessor="update__topic"
        )
    term = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="term", 
            accessor="update__term"
        )
    variable_1 = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="variable_1", 
            accessor="update__variable_1"
        )
    variable_2 = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="variable_2", 
            accessor="update__variable_2"
        )
    variable_3 = tables.Column(
            linkify=("change-update", [A("uuid")]),
            verbose_name="variable_3", 
            accessor="update__variable_3"
        )
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")


    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = [
            "category",
            "topic",
            "term",
            "variable_1",
            "variable_2",
            "variable_3",
            "status",
            "updated_at"
        ]