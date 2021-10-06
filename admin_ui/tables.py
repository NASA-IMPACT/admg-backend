from data_models.models import Campaign, Website
import django_tables2 as tables
from django_tables2 import A
from django.urls import reverse


from api_app.models import Change, UPDATE, CREATE


class ConditionalValueColumn(tables.Column):
    def __init__(self, update_accessor=None, **kwargs):
        super().__init__(**kwargs, empty_values=())
        self.update_accessor = update_accessor

    def render(self, **kwargs):
        record = kwargs.get("record")
        value = kwargs.get("value")

        if record.action == UPDATE:
            accessor = A(self.update_accessor)
            value = accessor.resolve(record)

        return value or "---"


class DraftLinkColumn(ConditionalValueColumn):

    def __init__(self, *args, **kwargs):
        self.update_viewname = kwargs.pop("update_viewname")
        self.viewname = kwargs.pop("viewname")
        self.url_kwargs = kwargs.pop("url_kwargs")

        super().__init__(*args, **kwargs)

    def get_url(self, **kwargs):
        record = kwargs.get("record")
        url_kwargs = {}
        for item in self.url_kwargs:
            url_kwargs[item] = getattr(record, self.url_kwargs[item])

        if record.action == UPDATE:
            return reverse(self.update_viewname, kwargs=url_kwargs)

        return reverse(self.viewname, kwargs=url_kwargs)


class DraftTableBase(tables.Table):
    draft_action = tables.Column(verbose_name="Draft Action", accessor="action")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    final_fields = ("draft_action", "status", "updated_at")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ("draft_action", "status", "updated_at")
        sequence = ("draft_action", "status", "updated_at")


class LimitedTableBase(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long name",
        accessor="update__long_name",
        update_accessor="content_object.long_name"
    )

    initial_fields = ('short_name', 'long_name')

    class Meta(DraftTableBase.Meta):
        fields = ('short_name', 'long_name')
        sequence = ('short_name', 'long_name')


class IOPChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    deployment = tables.Column(verbose_name="Deployment", accessor="update__deployment")
    start_date = tables.Column(verbose_name="Start Date", accessor="update__start_date")
    end_date = tables.Column(verbose_name="End Date", accessor="update__end_date")

    class Meta(DraftTableBase.Meta):
        all_fields = (
            'short_name',
            'deployment',
            'start_date',
            'end_date',
            ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class SignificantEventChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    deployment = tables.Column(verbose_name="Deployment", accessor="update__deployment")
    start_date = tables.Column(verbose_name="Start Date", accessor="update__start_date")
    end_date = tables.Column(verbose_name="End Date", accessor="update__end_date")

    class Meta(DraftTableBase.Meta):
        all_fields = (
            'short_name',
            'deployment',
            'start_date',
            'end_date',
            ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class CollectionPeriodChangeListTable(DraftTableBase):
    # TODO: have a calculated short_name field?
    deployment = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Deployment",
        accessor="update__deployment",
        update_accessor="content_object.short_name"
    )
    # deployment = tables.Column(verbose_name="Deployment", accessor="update__deployment")
    platform = tables.Column(verbose_name="Platform", accessor="update__platform")
    instruments = tables.Column(verbose_name="Instruments", accessor="update__instruments")

    class Meta(DraftTableBase.Meta):
        all_fields = (
            'deployment',
            'platform',
            'instruments',
            ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class DOIChangeListTable(DraftTableBase):
    concept_id = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Concept ID",
        accessor="update__concept_id",
        update_accessor="content_object.concept_id"
    )
    long_name = tables.Column(verbose_name="Long Name", accessor="update__long_name")

    class Meta(DraftTableBase.Meta):
        all_fields = (
            'concept_id',
            'long_name',
            ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class DeploymentChangeListTable(LimitedTableBase):

    campaign = tables.Column(verbose_name="Campaign", accessor="update__campaign")
    start_date = tables.Column(verbose_name="Start Date", accessor="update__start_date")
    end_date = tables.Column(verbose_name="End Date", accessor="update__end_date")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'campaign',
            'start_date',
            'end_date',
            ) + LimitedTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class PlatformTypeChangeListTable(LimitedTableBase):

    parent = tables.Column(verbose_name="Parent", accessor="update__parent")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'parent',
            ) + LimitedTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class MeasurementTypeChangeListTable(LimitedTableBase):
    parent = tables.Column(verbose_name="Parent", accessor="update__parent")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'parent',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class MeasurementStyleChangeListTable(LimitedTableBase):
    parent = tables.Column(verbose_name="Parent", accessor="update__parent")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'parent',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class HomeBaseChangeListTable(LimitedTableBase):
    location = tables.Column(verbose_name="Location", accessor="update__location")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'location',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class FocusAreaChangeListTable(LimitedTableBase):
    url = tables.Column(verbose_name="Url", accessor="update__url")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'url',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields

class SeasonChangeListTable(LimitedTableBase):
    
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class RepositoryChangeListTable(LimitedTableBase):
    gcmd_uuid = tables.Column(verbose_name="GCMD UUID", accessor="update__gcmd_uuid")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'gcmd_uuid',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class MeasurementRegionChangeListTable(LimitedTableBase):
    example = tables.Column(verbose_name="Example", accessor="update__example")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'example',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class GeographicalRegionChangeListTable(LimitedTableBase):
    example = tables.Column(verbose_name="Example", accessor="update__example")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'example',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class GeophysicalConceptChangeListTable(LimitedTableBase):
    example = tables.Column(verbose_name="Example", accessor="update__example")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'example',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields

class PartnerOrgChangeListTable(LimitedTableBase):
    website = tables.Column(verbose_name="Website", accessor="update__website")
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'website',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class WebsiteTypeChangeListTable(LimitedTableBase):
    
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class CampaignChangeListTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="campaign-detail",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    funding_agency = ConditionalValueColumn(
        verbose_name="Funding Agency",
        accessor="update__funding_agency",
        update_accessor="content_object.funding_agency"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            "funding_agency",
        ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class PlatformChangeListTable(LimitedTableBase):
    platform_type = tables.Column(
        verbose_name="Platform Type", accessor="platform_type_name"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + (
            'platform_type',
            ) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class InstrumentChangeListTable(LimitedTableBase):

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


# TODO: What is this and is it even used anywhere??
# class BasicChangeListTable(DraftTableBase):
#     short_name = tables.Column(
#         linkify=("change-update", [A("uuid")]),
#         verbose_name="Short Name",
#         accessor="update__short_name",
#     )
#     long_name = tables.Column(verbose_name="Long name", accessor="update__long_name")
#     status = tables.Column(verbose_name="Status", accessor="status")
#     updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

#     class Meta:
#         model = Change
#         attrs = {
#             "class": "table table-striped",
#             "thead": {"class": "table-primary"},
#             "th": {"style": "min-width: 10em"},
#         }
#         fields = ["short_name", "long_name", "status", "updated_at"]


# TODO: does this actually need to link to the campaign detail page?
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
    title = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Title",
        accessor="update__title",
        update_accessor="content_object.title"
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
        sequence = ("title", "url", "website_type", "status", "updated_at")


class CampaignWebsiteChangeListTable(DraftTableBase):
    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }


class AliasChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
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
        sequence = ("short_name", "model_type", "status", "updated_at")


class GcmdProjectChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    long_name = tables.Column(verbose_name="Long Name", accessor="update__long_name")
    bucket = tables.Column(verbose_name="Bucket", accessor="update__bucket")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "status", "updated_at", "bucket",]
        sequence = ("short_name", "long_name", "bucket", "status", "updated_at", )


class GcmdInstrumentChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    long_name = tables.Column(verbose_name="Long Name", accessor="update__long_name")
    instrument_category = tables.Column(verbose_name="Instrument Category", accessor="update__instrument_category")
    instrument_class = tables.Column(verbose_name="Instrument Class", accessor="update__instrument_class")
    instrument_type = tables.Column(verbose_name="Instrument Type", accessor="update__instrument_type")
    instrument_subtype = tables.Column(verbose_name="Instrument Subtype", accessor="update__instrument_subtype")
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
        sequence = (
            "short_name",
            "long_name",
            "instrument_subtype",
            "instrument_type",
            "instrument_class",
            "instrument_category",
            "status",
            "updated_at",
        )


class GcmdPlatformChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name"
    )
    long_name = tables.Column(verbose_name="Long Name", accessor="update__long_name")
    category = tables.Column(verbose_name="Category", accessor="update__category")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ["short_name", "long_name", "category", "status", "updated_at"]
        sequence = ("short_name", "long_name",  "category", "status", "updated_at")


class GcmdPhenomenaChangeListTable(DraftTableBase):
    variable_3 = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={'pk': "uuid"},
        verbose_name="Variable 3",
        accessor="update__variable_3",
        update_accessor="content_object.variable_3"
    )
    variable_2 = tables.Column(verbose_name="Variable 2", accessor="update__variable_2")
    variable_1 = tables.Column(verbose_name="Variable 1", accessor="update__variable_1")
    term = tables.Column(verbose_name="Term", accessor="update__term")
    topic = tables.Column(verbose_name="Topic", accessor="update__topic")
    category = tables.Column(verbose_name="Category", accessor="update__category")
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
        sequence = (
            "variable_3",
            "variable_2",
            "variable_1",
            "term",
            "topic",
            "category",
            "status",
            "updated_at"
        )
