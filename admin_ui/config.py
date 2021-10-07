from api_app.urls import camel_to_snake
from data_models import models

from . import published_tables
from . import tables

from .published_filters import GenericPublishedListFilter

MODEL_CONFIG_MAP = {
    "PlatformType": {
        "display_name": "Platform Type",
        "plural_snake_case": "platform_types",
        "admin_required_to_view": True,
    },
    "MeasurementType": {
        "display_name": "Measurement Type",
        "plural_snake_case": "measurement_types",
        "admin_required_to_view": True,
    },
    "MeasurementStyle": {
        "display_name": "Measurement Style",
        "plural_snake_case": "measurement_styles",
        "admin_required_to_view": True,
    },
    "HomeBase": {
        "display_name": "Home Base",
        "plural_snake_case": "home_bases",
        "admin_required_to_view": True,
    },
    "FocusArea": {
        "display_name": "Focus Area",
        "plural_snake_case": "focus_areas",
        "admin_required_to_view": True,
    },
    "Season": {
        "display_name": "Season",
        "plural_snake_case": "seasons",
        "admin_required_to_view": True,
    },
    "Repository": {
        "display_name": "Repository",
        "plural_snake_case": "repositories",
        "admin_required_to_view": True,
    },
    "MeasurementRegion": {
        "display_name": "Measurement Region",
        "plural_snake_case": "measurement_regions",
        "admin_required_to_view": True,
    },
    "GeographicalRegion": {
        "display_name": "Geographical Region",
        "plural_snake_case": "geographical_regions",
        "admin_required_to_view": True,
    },
    "GeophysicalConcept": {
        "display_name": "Geophysical Concept",
        "plural_snake_case": "geophysical_concepts",
        "admin_required_to_view": True,
    },
    "PartnerOrg": {
        "display_name": "Partner Org",
        "plural_snake_case": "partner_orgs",
        "admin_required_to_view": False,
    },
    "Alias": {
        "display_name": "Alias",
        "plural_snake_case": "aliases",
        "admin_required_to_view": False,
    },
    "GcmdProject": {
        "display_name": "GCMD Project",
        "plural_snake_case": "gcmd_projects",
        "admin_required_to_view": True,
    },
    "GcmdInstrument": {
        "display_name": "GCMD Instrument",
        "plural_snake_case": "gcmd_instruments",
        "admin_required_to_view": True,
    },
    "GcmdPlatform": {
        "display_name": "GCMD Platform",
        "plural_snake_case": "gcmd_platforms",
        "admin_required_to_view": True,
    },
    "GcmdPhenomena": {
        "display_name": "GCMD Phenomena",
        "plural_snake_case": "gcmd_phenomena",
        "admin_required_to_view": True,
    },
    "DOI": {
        "display_name": "DOI",
        "plural_snake_case": "dois",
        "admin_required_to_view": False,
    },
    "Campaign": {
        "display_name": "Campaign",
        "plural_snake_case": "campaigns",
        "admin_required_to_view": False,
    },
    "Platform": {
        "display_name": "Platform",
        "plural_snake_case": "platforms",
        "admin_required_to_view": False,
    },
    "Instrument": {
        "display_name": "Instrument",
        "plural_snake_case": "instruments",
        "admin_required_to_view": False,
    },
    "Deployment": {
        "display_name": "Deployment",
        "plural_snake_case": "deployments",
        "admin_required_to_view": False,
    },
    "IOP": {
        "display_name": "IOP",
        "plural_snake_case": "iops",
        "admin_required_to_view": False,
    },
    "SignificantEvent": {
        "display_name": "Significant Event",
        "plural_snake_case": "significant_events",
        "admin_required_to_view": False,
    },
    "CollectionPeriod": {
        "display_name": "C-D-P-I",
        "plural_snake_case": "collection_periods",
        "admin_required_to_view": False,
    },
    "Website": {
        "display_name": "Website",
        "plural_snake_case": "websites",
        "admin_required_to_view": False,
    },
    "WebsiteType": {
        "display_name": "Website Type",
        "plural_snake_case": "website_types",
        "admin_required_to_view": True,
    },
    "CampaignWebsite": {
        "display_name": "Campaign Website Linkage",
        "plural_snake_case": "campaign_websites",
        "admin_required_to_view": True,
    },
}

for model_name in MODEL_CONFIG_MAP.keys():
    MODEL_CONFIG_MAP[model_name]['singular_snake_case'] = camel_to_snake(model_name)
    MODEL_CONFIG_MAP[model_name]['filter'] = GenericPublishedListFilter(model_name)
    MODEL_CONFIG_MAP[model_name]['model'] = getattr(models, model_name)
    MODEL_CONFIG_MAP[model_name]['table'] = getattr(published_tables, f'Published{model_name}Table'),
    MODEL_CONFIG_MAP[model_name]['change_list_table'] = getattr(tables, f'{model_name}ChangeListTable')
