from data_models.models import Campaign, Website
import django_tables2 as tables
from django_tables2 import A

from data_models.models import (
    Campaign,
    Platform,
    Website,
    Alias,
    Instrument,
    GcmdInstrument
)

from api_app.urls import camel_to_snake


# TODO: ADD columns specific to the model

class PublishedPlatformTypeTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('PlatformType')}-detail-published", [A("uuid")]),
    )
class PublishedMeasurementTypeTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('MeasurementType')}-detail-published", [A("uuid")]),
    )
class PublishedMeasurementStyleTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('MeasurementStyle')}-detail-published", [A("uuid")]),
    )
class PublishedHomeBaseTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('HomeBase')}-detail-published", [A("uuid")]),
    )
class PublishedFocusAreaTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('FocusArea')}-detail-published", [A("uuid")]),
    )
class PublishedSeasonTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Season')}-detail-published", [A("uuid")]),
    )
class PublishedRepositoryTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Repository')}-detail-published", [A("uuid")]),
    )
class PublishedMeasurementRegionTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('MeasurementRegion')}-detail-published", [A("uuid")]),
    )
class PublishedGeographicalRegionTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('GeographicalRegion')}-detail-published", [A("uuid")]),
    )
class PublishedGeophysicalConceptTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('GeophysicalConcept')}-detail-published", [A("uuid")]),
    )
class PublishedPartnerOrgTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('PartnerOrg')}-detail-published", [A("uuid")]),
    )
class PublishedAliasTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Alias')}-detail-published", [A("uuid")]),
    )
class PublishedGcmdProjectTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('GcmdProject')}-detail-published", [A("uuid")]),
    )
class PublishedGcmdInstrumentTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('GcmdInstrument')}-detail-published", [A("uuid")]),
    )
class PublishedGcmdPlatformTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('GcmdPlatform')}-detail-published", [A("uuid")]),
    )
class PublishedGcmdPhenomenaTable(tables.Table):
    category = tables.Column(
        linkify=(f"mi-{camel_to_snake('GcmdPhenomena')}-detail-published", [A("uuid")]),
    )
class PublishedDOITable(tables.Table):
    concept_id = tables.Column(
        linkify=(f"mi-{camel_to_snake('DOI')}-detail-published", [A("uuid")]),
    )
class PublishedCampaignTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Campaign')}-detail-published", [A("uuid")]),
    )
class PublishedPlatformTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Platform')}-detail-published", [A("uuid")]),
    )
class PublishedInstrumentTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Instrument')}-detail-published", [A("uuid")]),
    )
class PublishedDeploymentTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('Deployment')}-detail-published", [A("uuid")]),
    )
class PublishedIOPTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('IOP')}-detail-published", [A("uuid")]),
    )
class PublishedSignificantEventTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('SignificantEvent')}-detail-published", [A("uuid")]),
    )
class PublishedCollectionPeriodTable(tables.Table):
    uuid = tables.Column(
        linkify=(f"mi-{camel_to_snake('CollectionPeriod')}-detail-published", [A("uuid")]),
    )
class PublishedWebsiteTable(tables.Table):
    uuid = tables.Column(
        linkify=(f"mi-{camel_to_snake('Website')}-detail-published", [A("uuid")]),
    )
class PublishedWebsiteTypeTable(tables.Table):
    short_name = tables.Column(
        linkify=(f"mi-{camel_to_snake('WebsiteType')}-detail-published", [A("uuid")]),
    )
class PublishedCampaignWebsiteTable(tables.Table):
    website = tables.Column(
        linkify=(f"mi-{camel_to_snake('CampaignWebsite')}-detail-published", [A("uuid")]),
    )
