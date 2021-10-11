from api_app.urls import camel_to_snake
from data_models import models

from . import published_tables
from . import tables

from .published_filters import GenericPublishedListFilter

model_names = [
    "PlatformType",
    "MeasurementType",
    "MeasurementStyle",
    "HomeBase",
    "FocusArea",
    "Season",
    "Repository",
    "MeasurementRegion",
    "GeographicalRegion",
    "GeophysicalConcept",
    "PartnerOrg",
    "Alias",
    "GcmdProject",
    "GcmdInstrument",
    "GcmdPlatform",
    "GcmdPhenomena",
    "DOI",
    "Campaign",
    "Platform",
    "Instrument",
    "Deployment",
    "IOP",
    "SignificantEvent",
    "CollectionPeriod",
    "Website",
    "WebsiteType",
    "CampaignWebsite",
]

MODEL_CONFIG_MAP = {}

for model_name in model_names:
    MODEL_CONFIG_MAP[model_name] = {}
    MODEL_CONFIG_MAP[model_name]["singular_snake_case"] = camel_to_snake(model_name)
    MODEL_CONFIG_MAP[model_name]["filter"] = GenericPublishedListFilter(model_name)
    MODEL_CONFIG_MAP[model_name]["model"] = getattr(models, model_name)
    MODEL_CONFIG_MAP[model_name]["table"] = getattr(
        published_tables, f"Published{model_name}Table"
    )
    MODEL_CONFIG_MAP[model_name]["change_list_table"] = getattr(
        tables, f"{model_name}ChangeListTable"
    )

MODEL_CONFIG_MAP = {
    "PlatformType": {
        **MODEL_CONFIG_MAP["PlatformType"],
        "display_name": "Platform Type",
        "plural_snake_case": "platform_types",
        "admin_required_to_view": True,
    },
    "MeasurementType": {
        **MODEL_CONFIG_MAP["MeasurementType"],
        "display_name": "Measurement Type",
        "plural_snake_case": "measurement_types",
        "admin_required_to_view": True,
    },
    "MeasurementStyle": {
        **MODEL_CONFIG_MAP["MeasurementStyle"],
        "display_name": "Measurement Style",
        "plural_snake_case": "measurement_styles",
        "admin_required_to_view": True,
    },
    "HomeBase": {
        **MODEL_CONFIG_MAP["HomeBase"],
        "display_name": "Home Base",
        "plural_snake_case": "home_bases",
        "admin_required_to_view": True,
    },
    "FocusArea": {
        **MODEL_CONFIG_MAP["FocusArea"],
        "display_name": "Focus Area",
        "plural_snake_case": "focus_areas",
        "admin_required_to_view": True,
    },
    "Season": {
        **MODEL_CONFIG_MAP["Season"],
        "display_name": "Season",
        "plural_snake_case": "seasons",
        "admin_required_to_view": True,
    },
    "Repository": {
        **MODEL_CONFIG_MAP["Repository"],
        "display_name": "Repository",
        "plural_snake_case": "repositories",
        "admin_required_to_view": True,
    },
    "MeasurementRegion": {
        **MODEL_CONFIG_MAP["MeasurementRegion"],
        "display_name": "Measurement Region",
        "plural_snake_case": "measurement_regions",
        "admin_required_to_view": True,
    },
    "GeographicalRegion": {
        **MODEL_CONFIG_MAP["GeographicalRegion"],
        "display_name": "Geographical Region",
        "plural_snake_case": "geographical_regions",
        "admin_required_to_view": True,
    },
    "GeophysicalConcept": {
        **MODEL_CONFIG_MAP["GeophysicalConcept"],
        "display_name": "Geophysical Concept",
        "plural_snake_case": "geophysical_concepts",
        "admin_required_to_view": True,
    },
    "PartnerOrg": {
        **MODEL_CONFIG_MAP["PartnerOrg"],
        "display_name": "Partner Org",
        "plural_snake_case": "partner_orgs",
        "admin_required_to_view": False,
    },
    "Alias": {
        **MODEL_CONFIG_MAP["Alias"],
        "display_name": "Alias",
        "plural_snake_case": "aliases",
        "admin_required_to_view": False,
    },
    "GcmdProject": {
        **MODEL_CONFIG_MAP["GcmdProject"],
        "display_name": "GCMD Project",
        "plural_snake_case": "gcmd_projects",
        "admin_required_to_view": True,
    },
    "GcmdInstrument": {
        **MODEL_CONFIG_MAP["GcmdInstrument"],
        "display_name": "GCMD Instrument",
        "plural_snake_case": "gcmd_instruments",
        "admin_required_to_view": True,
    },
    "GcmdPlatform": {
        **MODEL_CONFIG_MAP["GcmdPlatform"],
        "display_name": "GCMD Platform",
        "plural_snake_case": "gcmd_platforms",
        "admin_required_to_view": True,
    },
    "GcmdPhenomena": {
        **MODEL_CONFIG_MAP["GcmdPhenomena"],
        "display_name": "GCMD Phenomena",
        "plural_snake_case": "gcmd_phenomena",
        "admin_required_to_view": True,
    },
    "DOI": {
        **MODEL_CONFIG_MAP["DOI"],
        "display_name": "DOI",
        "plural_snake_case": "dois",
        "admin_required_to_view": False,
    },
    "Campaign": {
        **MODEL_CONFIG_MAP["Campaign"],
        "display_name": "Campaign",
        "plural_snake_case": "campaigns",
        "admin_required_to_view": False,
    },
    "Platform": {
        **MODEL_CONFIG_MAP["Platform"],
        "display_name": "Platform",
        "plural_snake_case": "platforms",
        "admin_required_to_view": False,
    },
    "Instrument": {
        **MODEL_CONFIG_MAP["Instrument"],
        "display_name": "Instrument",
        "plural_snake_case": "instruments",
        "admin_required_to_view": False,
    },
    "Deployment": {
        **MODEL_CONFIG_MAP["Deployment"],
        "display_name": "Deployment",
        "plural_snake_case": "deployments",
        "admin_required_to_view": False,
    },
    "IOP": {
        **MODEL_CONFIG_MAP["IOP"],
        "display_name": "IOP",
        "plural_snake_case": "iops",
        "admin_required_to_view": False,
    },
    "SignificantEvent": {
        **MODEL_CONFIG_MAP["SignificantEvent"],
        "display_name": "Significant Event",
        "plural_snake_case": "significant_events",
        "admin_required_to_view": False,
    },
    "CollectionPeriod": {
        **MODEL_CONFIG_MAP["CollectionPeriod"],
        "display_name": "C-D-P-I",
        "plural_snake_case": "collection_periods",
        "admin_required_to_view": False,
    },
    "Website": {
        **MODEL_CONFIG_MAP["Website"],
        "display_name": "Website",
        "plural_snake_case": "websites",
        "admin_required_to_view": False,
    },
    "WebsiteType": {
        **MODEL_CONFIG_MAP["WebsiteType"],
        "display_name": "Website Type",
        "plural_snake_case": "website_types",
        "admin_required_to_view": True,
    },
    "CampaignWebsite": {
        **MODEL_CONFIG_MAP["CampaignWebsite"],
        "display_name": "Campaign Website Linkage",
        "plural_snake_case": "campaign_websites",
        "admin_required_to_view": True,
    },
}
