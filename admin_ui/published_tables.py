import django_tables2 as tables
from api_app.urls import camel_to_snake
from data_models.models import (
    DOI,
    IOP,
    Alias,
    Campaign,
    CollectionPeriod,
    Deployment,
    FocusArea,
    GcmdInstrument,
    GcmdPhenomena,
    GcmdPlatform,
    GcmdProject,
    GeographicalRegion,
    GeophysicalConcept,
    HomeBase,
    Instrument,
    MeasurementRegion,
    MeasurementStyle,
    MeasurementType,
    PartnerOrg,
    Platform,
    Repository,
    Season,
    SignificantEvent,
    Website,
    WebsiteType,
)
from django_tables2 import A

from .tables import (
    DraftLinkColumn,
    ShortNamefromUUIDColumn,
    ShortNamefromUUIDLinkColumn,
)


class LimitedTableBase(tables.Table):
    long_name = tables.Column(
        verbose_name="Long name",
        accessor="long_name",
    )

    initial_fields = ("short_name", "long_name")

    class Meta:
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }


class IOPPublishedTable(tables.Table):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('IOP')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="deployment",
    )
    start_date = tables.Column(
        verbose_name="Start Date",
        accessor="start_date",
    )
    end_date = tables.Column(
        verbose_name="End Date",
        accessor="end_date",
    )

    class Meta(LimitedTableBase.Meta):
        fields = ["short_name", "deployment", "start_date", "end_date"]
        sequence = fields
        model = IOP


class SignificantEventPublishedTable(tables.Table):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('SignificantEvent')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="deployment",
    )
    start_date = tables.Column(
        verbose_name="Start Date",
        accessor="start_date",
    )
    end_date = tables.Column(
        verbose_name="End Date",
        accessor="end_date",
    )

    class Meta(LimitedTableBase.Meta):
        model = SignificantEvent
        fields = (
            "short_name",
            "deployment",
            "start_date",
            "end_date",
        )
        sequence = fields


class CollectionPeriodPublishedTable(tables.Table):
    deployment = ShortNamefromUUIDLinkColumn(
        viewname=f"{camel_to_snake('CollectionPeriod')}-detail-published",
        url_kwargs={"pk": "uuid"},
        model=Deployment,
        verbose_name="Deployment",
        accessor="deployment",
    )

    platform = ShortNamefromUUIDColumn(
        verbose_name="Platform",
        model=Platform,
        accessor="platform",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="instruments",
    )

    class Meta(LimitedTableBase.Meta):
        model = CollectionPeriod
        fields = (
            "deployment",
            "platform",
            "instruments",
        )
        sequence = fields


class DOIPublishedTable(tables.Table):
    concept_id = DraftLinkColumn(
        viewname=f"{camel_to_snake('DOI')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Concept ID",
        accessor="concept_id",
    )
    long_name = tables.Column(
        verbose_name="Long name",
        accessor="long_name",
    )
    campaigns = ShortNamefromUUIDColumn(
        verbose_name="Campaigns",
        model=Campaign,
        accessor="campaigns",
    )
    platforms = ShortNamefromUUIDColumn(
        verbose_name="Platforms",
        model=Platform,
        accessor="platforms",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="instruments",
    )

    class Meta(LimitedTableBase.Meta):
        model = DOI
        fields = (
            "concept_id",
            "long_name",
            "campaigns",
            "platforms",
            "instruments",
        )
        sequence = fields


class DeploymentPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Deployment')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    campaign = ShortNamefromUUIDColumn(
        verbose_name="Campaign",
        model=Campaign,
        accessor="campaign",
    )
    start_date = tables.Column(
        verbose_name="Start Date",
        accessor="start_date",
    )
    end_date = tables.Column(
        verbose_name="End Date",
        accessor="end_date",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + (
            "campaign",
            "start_date",
            "end_date",
        )
        sequence = fields
        model = Deployment


class PlatformTypePublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('PlatformType')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("parent",)
        sequence = fields
        model = Platform


class MeasurementTypePublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('MeasurementType')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("parent",)
        sequence = fields
        model = MeasurementType


class MeasurementStylePublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('MeasurementStyle')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("parent",)
        sequence = fields
        model = MeasurementStyle


class HomeBasePublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('HomeBase')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    location = tables.Column(verbose_name="Location", accessor="location")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("location",)
        sequence = fields
        model = HomeBase


class FocusAreaPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('FocusArea')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    url = tables.Column(verbose_name="Url", accessor="url")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("url",)
        sequence = fields
        model = FocusArea


class SeasonPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Season')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields
        fields = fields
        sequence = fields
        model = Season


class RepositoryPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Repository')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    gcmd_uuid = tables.Column(verbose_name="GCMD UUID", accessor="gcmd_uuid")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("gcmd_uuid",)
        sequence = fields
        model = Repository


class MeasurementRegionPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('MeasurementRegion')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    example = tables.Column(verbose_name="Example", accessor="example")
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("example",)
        sequence = fields
        model = MeasurementRegion


class GeographicalRegionPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('GeographicalRegion')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    example = tables.Column(verbose_name="Example", accessor="example")
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("example",)
        sequence = fields
        model = GeographicalRegion


class GeophysicalConceptPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('GeophysicalConcept')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    example = tables.Column(verbose_name="Example", accessor="example")
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("example",)
        sequence = fields
        model = GeophysicalConcept


class PartnerOrgPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('PartnerOrg')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    website = tables.Column(verbose_name="Website", accessor="website")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("website",)
        sequence = fields
        model = PartnerOrg


class WebsiteTypePublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('WebsiteType')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields
        fields = fields
        sequence = fields
        model = WebsiteType


class CampaignPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Campaign')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    funding_agency = tables.Column(verbose_name="Funding Agency", accessor="funding_agency")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("funding_agency",)
        sequence = fields
        model = Campaign


class PlatformPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Platform')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    platform_type = tables.Column(verbose_name="Platform Type", accessor="platform_type")

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields + ("platform_type",)
        sequence = fields
        model = Platform


class InstrumentPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Instrument')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )

    class Meta(LimitedTableBase.Meta):
        fields = LimitedTableBase.initial_fields
        fields = fields
        sequence = fields
        model = Instrument


class WebsitePublishedTable(LimitedTableBase):
    title = DraftLinkColumn(
        viewname="{camel_to_snake('Website')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    url = tables.Column(verbose_name="URL", accessor="url")
    website_type = tables.Column(verbose_name="Website Type", accessor="website_type_name")

    class Meta(LimitedTableBase.Meta):
        fields = (
            "title",
            "url",
            "website_type",
        )
        sequence = fields
        model_name = Website


class AliasPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('Alias')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    # TODO replace model_type which short_name of related object
    model_type = tables.Column(verbose_name="Item Type", accessor="model_name")

    class Meta(LimitedTableBase.Meta):
        fields = (
            "short_name",
            "model_type",
        )
        sequence = fields
        model = Alias


class GcmdProjectPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('GcmdProject')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    bucket = tables.Column(verbose_name="Bucket", accessor="bucket")

    class Meta(LimitedTableBase.Meta):
        fields = (
            "short_name",
            "long_name",
            "bucket",
        )
        sequence = fields
        model = GcmdProject


class GcmdInstrumentPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('GcmdInstrument')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    instrument_category = tables.Column(
        verbose_name="Instrument Category", accessor="instrument_category"
    )
    instrument_class = tables.Column(verbose_name="Instrument Class", accessor="instrument_class")
    instrument_type = tables.Column(verbose_name="Instrument Type", accessor="instrument_type")
    instrument_subtype = tables.Column(
        verbose_name="Instrument Subtype", accessor="instrument_subtype"
    )

    class Meta(LimitedTableBase.Meta):
        fields = (
            "short_name",
            "long_name",
            "instrument_category",
            "instrument_class",
            "instrument_type",
            "instrument_subtype",
        )
        sequence = fields
        model = GcmdInstrument


class GcmdPlatformPublishedTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        viewname=f"{camel_to_snake('GcmdPlatform')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="short_name",
    )
    category = tables.Column(verbose_name="Category", accessor="category")

    class Meta(LimitedTableBase.Meta):
        fields = (
            "short_name",
            "long_name",
            "category",
        )
        sequence = fields
        model = GcmdPlatform


class GcmdPhenomenaPublishedTable(tables.Table):
    variable_3 = DraftLinkColumn(
        viewname=f"{camel_to_snake('GcmdPhenomena')}-detail-published",
        url_kwargs={"pk": "uuid"},
        verbose_name="Variable 3",
        accessor="short_name",
    )
    variable_2 = tables.Column(verbose_name="Variable 2", accessor="variable_2")
    variable_1 = tables.Column(verbose_name="Variable 1", accessor="variable_1")
    term = tables.Column(verbose_name="Term", accessor="term")
    topic = tables.Column(verbose_name="Topic", accessor="topic")
    category = tables.Column(verbose_name="Category", accessor="category")

    class Meta(LimitedTableBase.Meta):
        fields = (
            "variable_3",
            "variable_2",
            "variable_1",
            "term",
            "topic",
            "category",
        )
        sequence = fields
        model = GcmdPhenomena
