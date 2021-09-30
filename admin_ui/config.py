from data_models.models import (
    PlatformType,
    MeasurementType,
    MeasurementStyle,
    HomeBase,
    FocusArea,
    Season,
    Repository,
    MeasurementRegion,
    GeographicalRegion,
    GeophysicalConcept,
    PartnerOrg,
    Alias,
    GcmdProject,
    GcmdInstrument,
    GcmdPlatform,
    GcmdPhenomena,
    DOI,
    Campaign,
    Platform,
    Instrument,
    Deployment,
    IOP,
    SignificantEvent,
    CollectionPeriod,
    Website,
    WebsiteType,
    CampaignWebsite,
)

from .published_tables import (
    PublishedPlatformTypeTable,
    PublishedMeasurementTypeTable,
    PublishedMeasurementStyleTable,
    PublishedHomeBaseTable,
    PublishedFocusAreaTable,
    PublishedSeasonTable,
    PublishedRepositoryTable,
    PublishedMeasurementRegionTable,
    PublishedGeographicalRegionTable,
    PublishedGeophysicalConceptTable,
    PublishedPartnerOrgTable,
    PublishedAliasTable,
    PublishedGcmdProjectTable,
    PublishedGcmdInstrumentTable,
    PublishedGcmdPlatformTable,
    PublishedGcmdPhenomenaTable,
    PublishedDOITable,
    PublishedCampaignTable,
    PublishedPlatformTable,
    PublishedInstrumentTable,
    PublishedDeploymentTable,
    PublishedIOPTable,
    PublishedSignificantEventTable,
    PublishedCollectionPeriodTable,
    PublishedWebsiteTable,
    PublishedWebsiteTypeTable,
    PublishedCampaignWebsiteTable,
)
from .tables import *
from .published_filters import GenericPublishedListFilter

from api_app.urls import camel_to_snake

MODEL_CONFIG_MAP = {
    "PlatformType": {
        "singular_snake_case": camel_to_snake("PlatformType"),
        "plural_snake_case": "platform_types",
        "model": PlatformType,
        "table": PublishedPlatformTypeTable,
        "change_list_table": PlatformTypeChangeListTable,
        "filter": GenericPublishedListFilter("PlatformType"),
    },
    "MeasurementType": {
        "singular_snake_case": camel_to_snake("MeasurementType"),
        "plural_snake_case": "measurement_types",
        "model": MeasurementType,
        "table": PublishedMeasurementTypeTable,
        "change_list_table": MeasurementTypeChangeListTable,
        "filter": GenericPublishedListFilter("MeasurementType"),
    },
    "MeasurementStyle": {
        "singular_snake_case": camel_to_snake("MeasurementStyle"),
        "plural_snake_case": "measurement_styles",
        "model": MeasurementStyle,
        "table": PublishedMeasurementStyleTable,
        "change_list_table": MeasurementStyleChangeListTable,
        "filter": GenericPublishedListFilter("MeasurementStyle"),
    },
    "HomeBase": {
        "singular_snake_case": camel_to_snake("HomeBase"),
        "plural_snake_case": "home_bases",
        "model": HomeBase,
        "table": PublishedHomeBaseTable,
        "change_list_table": HomeBaseChangeListTable,
        "filter": GenericPublishedListFilter("HomeBase"),
    },
    "FocusArea": {
        "singular_snake_case": camel_to_snake("FocusArea"),
        "plural_snake_case": "focus_areas",
        "model": FocusArea,
        "table": PublishedFocusAreaTable,
        "change_list_table": FocusAreaChangeListTable,
        "filter": GenericPublishedListFilter("FocusArea"),
    },
    "Season": {
        "singular_snake_case": camel_to_snake("Season"),
        "plural_snake_case": "seasons",
        "model": Season,
        "table": PublishedSeasonTable,
        "change_list_table": SeasonChangeListTable,
        "filter": GenericPublishedListFilter("Season"),
    },
    "Repository": {
        "singular_snake_case": camel_to_snake("Repository"),
        "plural_snake_case": "repositories",
        "model": Repository,
        "table": PublishedRepositoryTable,
        "change_list_table": RepositoryChangeListTable,
        "filter": GenericPublishedListFilter("Repository"),
    },
    "MeasurementRegion": {
        "singular_snake_case": camel_to_snake("MeasurementRegion"),
        "plural_snake_case": "measurement_regions",
        "model": MeasurementRegion,
        "table": PublishedMeasurementRegionTable,
        "change_list_table": MeasurementRegionChangeListTable,
        "filter": GenericPublishedListFilter("MeasurementRegion"),
    },
    "GeographicalRegion": {
        "singular_snake_case": camel_to_snake("GeographicalRegion"),
        "plural_snake_case": "geographical_regions",
        "model": GeographicalRegion,
        "table": PublishedGeographicalRegionTable,
        "change_list_table": GeographicalRegionChangeListTable,
        "filter": GenericPublishedListFilter("GeographicalRegion"),
    },
    "GeophysicalConcept": {
        "singular_snake_case": camel_to_snake("GeophysicalConcept"),
        "plural_snake_case": "geophysical_concepts",
        "model": GeophysicalConcept,
        "table": PublishedGeophysicalConceptTable,
        "change_list_table": GeophysicalConceptChangeListTable,
        "filter": GenericPublishedListFilter("GeophysicalConcept"),
    },
    "PartnerOrg": {
        "singular_snake_case": camel_to_snake("PartnerOrg"),
        "plural_snake_case": "partner_orgs",
        "model": PartnerOrg,
        "table": PublishedPartnerOrgTable,
        "change_list_table": PartnerOrgChangeListTable,
        "filter": GenericPublishedListFilter("PartnerOrg"),
    },
    "Alias": {
        "singular_snake_case": camel_to_snake("Alias"),
        "plural_snake_case": "aliases",
        "model": Alias,
        "table": PublishedAliasTable,
        "change_list_table": AliasChangeListTable,
        "filter": GenericPublishedListFilter("Alias"),
    },
    "GcmdProject": {
        "singular_snake_case": camel_to_snake("GcmdProject"),
        "plural_snake_case": "gcmd_projects",
        "model": GcmdProject,
        "table": PublishedGcmdProjectTable,
        "change_list_table": GcmdProjectChangeListTable,
        "filter": GenericPublishedListFilter("GcmdProject"),
    },
    "GcmdInstrument": {
        "singular_snake_case": camel_to_snake("GcmdInstrument"),
        "plural_snake_case": "gcmd_instruments",
        "model": GcmdInstrument,
        "table": PublishedGcmdInstrumentTable,
        "change_list_table": GcmdInstrumentChangeListTable,
        "filter": GenericPublishedListFilter("GcmdInstrument"),
    },
    "GcmdPlatform": {
        "singular_snake_case": camel_to_snake("GcmdPlatform"),
        "plural_snake_case": "gcmd_platforms",
        "model": GcmdPlatform,
        "table": PublishedGcmdPlatformTable,
        "change_list_table": GcmdPlatformChangeListTable,
        "filter": GenericPublishedListFilter("GcmdPlatform"),
    },
    "GcmdPhenomena": {
        "singular_snake_case": camel_to_snake("GcmdPhenomena"),
        "plural_snake_case": "gcmd_phenomena",
        "model": GcmdPhenomena,
        "table": PublishedGcmdPhenomenaTable,
        "change_list_table": GcmdPhenomenaChangeListTable,
        "filter": GenericPublishedListFilter("GcmdPhenomena"),
    },
    "DOI": {
        "singular_snake_case": camel_to_snake("DOI"),
        "plural_snake_case": "dois",
        "model": DOI,
        "table": PublishedDOITable,
        # "change_list_table": DOIChangeListTable,
        "filter": GenericPublishedListFilter("DOI"),
    },
    "Campaign": {
        "singular_snake_case": camel_to_snake("Campaign"),
        "plural_snake_case": "campaigns",
        "model": Campaign,
        "table": PublishedCampaignTable,
        "change_list_table": CampaignChangeListTable,
        "filter": GenericPublishedListFilter("Campaign"),
    },
    "Platform": {
        "singular_snake_case": camel_to_snake("Platform"),
        "plural_snake_case": "platforms",
        "model": Platform,
        "table": PublishedPlatformTable,
        "change_list_table": PlatformChangeListTable,
        "filter": GenericPublishedListFilter("Platform"),
    },
    "Instrument": {
        "singular_snake_case": camel_to_snake("Instrument"),
        "plural_snake_case": "instruments",
        "model": Instrument,
        "table": PublishedInstrumentTable,
        # "change_list_table": InstrumentChangeListTable,
        "filter": GenericPublishedListFilter("Instrument"),
    },
    "Deployment": {
        "singular_snake_case": camel_to_snake("Deployment"),
        "plural_snake_case": "deployments",
        "model": Deployment,
        "table": PublishedDeploymentTable,
        # "change_list_table": DeploymentChangeListTable,
        "filter": GenericPublishedListFilter("Deployment"),
    },
    "IOP": {
        "singular_snake_case": camel_to_snake("IOP"),
        "plural_snake_case": "iops",
        "model": IOP,
        "table": PublishedIOPTable,
        # "change_list_table": IOPChangeListTable,
        "filter": GenericPublishedListFilter("IOP"),
    },
    "SignificantEvent": {
        "singular_snake_case": camel_to_snake("SignificantEvent"),
        "plural_snake_case": "significant_events",
        "model": SignificantEvent,
        "table": PublishedSignificantEventTable,
        # "change_list_table": SignificantEventChangeListTable,
        "filter": GenericPublishedListFilter("SignificantEvent"),
    },
    "CollectionPeriod": {
        "singular_snake_case": camel_to_snake("CollectionPeriod"),
        "plural_snake_case": "collection_periods",
        "model": CollectionPeriod,
        "table": PublishedCollectionPeriodTable,
        # "change_list_table": CollectionPeriodChangeListTable,
        "filter": GenericPublishedListFilter("CollectionPeriod"),
    },
    "Website": {
        "singular_snake_case": camel_to_snake("Website"),
        "plural_snake_case": "websites",
        "model": Website,
        "table": PublishedWebsiteTable,
        "change_list_table": WebsiteChangeListTable,
        "filter": GenericPublishedListFilter("Website"),
    },
    "WebsiteType": {
        "singular_snake_case": camel_to_snake("WebsiteType"),
        "plural_snake_case": "website_types",
        "model": WebsiteType,
        "table": PublishedWebsiteTypeTable,
        "change_list_table": WebsiteTypeChangeListTable,
        "filter": GenericPublishedListFilter("WebsiteType"),
    },
    # "CampaignWebsite": {
    #     "singular_snake_case": camel_to_snake("CampaignWebsite"),
    #     "plural_snake_case": "campaign_websites",
    #     "model": CampaignWebsite,
    #     "table": PublishedCampaignWebsiteTable,
    # "change_list_table": "ChangeListTable,
    #     "filter": GenericPublishedListFilter(# "CampaignWebsite"),
    # },
}