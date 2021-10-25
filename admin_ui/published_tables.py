import django_tables2 as tables
from api_app.models import CREATE, UPDATE
from api_app.urls import camel_to_snake
from data_models.models import (
    DOI,
    IOP,
    Alias,
    Campaign,
    CampaignWebsite,
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

from .tables import ShortNamefromUUIDColumn, ShortNamefromUUIDLinkColumn


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
        fields = ("short_name", "long_name")
        sequence = ("short_name", "long_name")


class IOPPublishedTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('IOP')}-detail-published", [A("uuid")]),
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Platform,
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
        model = IOP
        all_fields = (
            "short_name",
            "deployment",
            "start_date",
            "end_date",
        )
        sequence = all_fields


class SignificantEventPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('SignificantEvent')}-detail-published", [A("uuid")]),
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Platform,
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
        all_fields = (
            "short_name",
            "deployment",
            "start_date",
            "end_date",
        )
        sequence = all_fields


class CollectionPeriodPublishedTable(LimitedTableBase):
    # TODO: have a calculated short_name field?
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('CollectionPeriod')}-detail-published", [A("uuid")]),
    )
    deployment = ShortNamefromUUIDLinkColumn(
        viewname=f"{camel_to_snake('CollectionPeriod')}-detail-published",
        url_kwargs={"pk": "uuid"},
        model=Deployment,
        verbose_name="Deployment",
        accessor="deployment",
        update_viewname="change-diff",
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
        all_fields = (
            "deployment",
            "platform",
            "instruments",
        )
        fields = list(all_fields)
        sequence = all_fields


class DOIPublishedTable(LimitedTableBase):
    concept_id = tables.Column(
        linkify=(f"{camel_to_snake('DOI')}-detail-published", [A("uuid")]),
    )
    campaigns = ShortNamefromUUIDColumn(
        verbose_name="Campaigns",
        model=Platform,
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
        all_fields = (
            "concept_id",
            "long_name",
            "campaigns",
            "platforms",
            "instruments",
        )
        fields = list(all_fields)
        sequence = all_fields


class DeploymentPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Deployment')}-detail-published", [A("uuid")]),
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
        all_fields = LimitedTableBase.initial_fields + (
            "campaign",
            "start_date",
            "end_date",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = Deployment


class PlatformTypePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('PlatformType')}-detail-published", [A("uuid")]),
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",)
        fields = list(all_fields)
        sequence = all_fields
        model = Platform


class MeasurementTypePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('MeasurementType')}-detail-published", [A("uuid")]),
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",)
        fields = list(all_fields)
        sequence = all_fields
        model = MeasurementType


class MeasurementStylePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('MeasurementStyle')}-detail-published", [A("uuid")]),
    )
    parent = tables.Column(
        verbose_name="Parent",
        accessor="parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",)
        fields = list(all_fields)
        sequence = all_fields
        model = MeasurementStyle


class HomeBasePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('HomeBase')}-detail-published", [A("uuid")]),
    )
    location = tables.Column(verbose_name="Location", accessor="location")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("location",)
        fields = all_fields
        sequence = all_fields
        model = HomeBase


class FocusAreaPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('FocusArea')}-detail-published", [A("uuid")]),
    )
    url = tables.Column(verbose_name="Url", accessor="url")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("url",)
        fields = all_fields
        sequence = all_fields
        model = FocusArea


class SeasonPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Season')}-detail-published", [A("uuid")]),
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields
        fields = all_fields
        sequence = all_fields
        model = Season


class RepositoryPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Repository')}-detail-published", [A("uuid")]),
    )
    gcmd_uuid = tables.Column(verbose_name="GCMD UUID", accessor="gcmd_uuid")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("gcmd_uuid",)
        fields = all_fields
        sequence = all_fields
        model = Repository


class MeasurementRegionPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(
            f"{camel_to_snake('MeasurementRegion')}-detail-published",
            [A("uuid")],
        ),
    )
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",)
        fields = all_fields
        sequence = all_fields
        model = MeasurementRegion


class GeographicalRegionPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(
            f"{camel_to_snake('GeographicalRegion')}-detail-published",
            [A("uuid")],
        ),
    )
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",)
        fields = all_fields
        sequence = all_fields
        model = GeographicalRegion


class GeophysicalConceptPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(
            f"{camel_to_snake('GeophysicalConcept')}-detail-published",
            [A("uuid")],
        ),
    )
    example = tables.Column(verbose_name="Example", accessor="example")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",)
        fields = all_fields
        sequence = all_fields
        model = GeophysicalConcept


class PartnerOrgPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('PartnerOrg')}-detail-published", [A("uuid")]),
    )
    website = tables.Column(verbose_name="Website", accessor="website")

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("website",)
        fields = all_fields
        sequence = all_fields
        model = PartnerOrg


class WebsiteTypePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('WebsiteType')}-detail-published", [A("uuid")]),
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields
        fields = all_fields
        sequence = all_fields
        model = WebsiteType


class CampaignPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Campaign')}-detail-published", [A("uuid")]),
    )
    funding_agency = tables.Column(
        verbose_name="Funding Agency", accessor="funding_agency"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("funding_agency",)
        fields = all_fields
        sequence = all_fields
        model = Campaign


class PlatformPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Platform')}-detail-published", [A("uuid")]),
    )
    platform_type = tables.Column(
        verbose_name="Platform Type", accessor="platform_type_name"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("platform_type",)
        fields = all_fields
        sequence = all_fields
        model = Platform


class InstrumentPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Instrument')}-detail-published", [A("uuid")]),
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields
        fields = all_fields
        sequence = all_fields
        model = Instrument


class WebsitePublishedTable(LimitedTableBase):
    title = tables.Column(
        linkify=(f"{camel_to_snake('Website')}-detail-published", [A("uuid")]),
    )
    url = tables.Column(verbose_name="URL", accessor="url")
    website_type = tables.Column(
        verbose_name="Website Type", accessor="website_type_name"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "title",
            "url",
            "website_type",
        )
        fields = list(all_fields)
        sequence = all_fields
        model_name = Website


class CampaignWebsitePublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('CampaignWebsite')}-detail-published", [A("uuid")]),
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields
        fields = list(all_fields)
        sequence = all_fields
        model = CampaignWebsite


class AliasPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('Alias')}-detail-published", [A("uuid")]),
    )
    # TODO replace model_type which short_name of related object
    model_type = tables.Column(verbose_name="Item Type", accessor="model_name")

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "short_name",
            "model_type",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = Alias


class GcmdProjectPublishedTable(LimitedTableBase):
    short_name = tables.Column(
        linkify=(f"{camel_to_snake('GcmdProject')}-detail-published", [A("uuid")]),
    )
    bucket = tables.Column(verbose_name="Bucket", accessor="bucket")

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "bucket",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = GcmdProject


class GcmdInstrumentPublishedTable(LimitedTableBase):
    short_name = short_name = tables.Column(
        linkify=(f"{camel_to_snake('GcmdInstrument')}-detail-published", [A("uuid")]),
    )
    instrument_category = tables.Column(
        verbose_name="Instrument Category", accessor="instrument_category"
    )
    instrument_class = tables.Column(
        verbose_name="Instrument Class", accessor="instrument_class"
    )
    instrument_type = tables.Column(
        verbose_name="Instrument Type", accessor="instrument_type"
    )
    instrument_subtype = tables.Column(
        verbose_name="Instrument Subtype", accessor="instrument_subtype"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "instrument_category",
            "instrument_class",
            "instrument_type",
            "instrument_subtype",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = GcmdInstrument


class GcmdPlatformPublishedTable(LimitedTableBase):
    short_name = short_name = tables.Column(
        linkify=(f"{camel_to_snake('GcmdPlatform')}-detail-published", [A("uuid")]),
    )
    category = tables.Column(verbose_name="Category", accessor="category")

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "category",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = GcmdPlatform


class GcmdPhenomenaPublishedTable(tables.Table):
    variable_3 = tables.Column(
        linkify=(f"{camel_to_snake('GcmdPhenomena')}-detail-published", [A("uuid")]),
    )
    variable_2 = tables.Column(verbose_name="Variable 2", accessor="variable_2")
    variable_1 = tables.Column(verbose_name="Variable 1", accessor="variable_1")
    term = tables.Column(verbose_name="Term", accessor="term")
    topic = tables.Column(verbose_name="Topic", accessor="topic")
    category = tables.Column(verbose_name="Category", accessor="category")

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            "variable_3",
            "variable_2",
            "variable_1",
            "term",
            "topic",
            "category",
        )
        fields = list(all_fields)
        sequence = all_fields
        model = GcmdPhenomena
