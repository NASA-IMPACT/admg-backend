from api_app.urls import camel_to_snake
from data_models import models

from . import tables

from .published_filters import GenericPublishedListFilter
from .published_tables import build_published_table


# any custom values for each model are added to this dictionary
# all models must be defined at a minimum with an empty dictionary
CUSTOM_MODEL_VALUES = {
    "PlatformType": {},
    "MeasurementType": {},
    "MeasurementStyle": {},
    "HomeBase": {},
    "FocusArea": {},
    "Season": {},
    "Repository": {},
    "MeasurementRegion": {},
    "GeographicalRegion": {},
    "GeophysicalConcept": {},
    "PartnerOrg": {
        "admin_required_to_view": False,
    },
    "Alias": {
        "admin_required_to_view": False,
    },
    "GcmdProject": {
        "display_name": "GCMD Project",
    },
    "GcmdInstrument": {
        "display_name": "GCMD Instrument",
    },
    "GcmdPlatform": {
        "display_name": "GCMD Platform",
    },
    "GcmdPhenomena": {
        "display_name": "GCMD Phenomena",
        "table_link_field": "category",
    },
    "DOI": {
        "admin_required_to_view": False,
        "table_link_field": "concept_id",
    },
    "Campaign": {
        "admin_required_to_view": False,
    },
    "Platform": {
        "admin_required_to_view": False,
    },
    "Instrument": {
        "admin_required_to_view": False,
    },
    "Deployment": {
        "admin_required_to_view": False,
    },
    "IOP": {
        "admin_required_to_view": False,
    },
    "SignificantEvent": {
        "admin_required_to_view": False,
    },
    "CollectionPeriod": {
        "display_name": "C-D-P-I",
        "admin_required_to_view": False,
        "table_link_field": "uuid",
    },
    "Website": {
        "admin_required_to_view": False,
        "table_link_field": "uuid",
    },
    "WebsiteType": {},
    "CampaignWebsite": {
        "display_name": "Campaign Website Linkage",
        "table_link_field": "website",
    },
}

# defaults are assigned to each model in this comprehension, and then overwritten by the above dictionary
MODEL_CONFIG_MAP = {
    model_name: {
        "filter": GenericPublishedListFilter(model_name),
        "model": getattr(models, model_name),
        "table": build_published_table(
            model_name, overrides.get("table_link_field", "short_name")
        ),
        "change_list_table": getattr(tables, f"{model_name}ChangeListTable"),
        "display_name": getattr(models, model_name)._meta.verbose_name.title(),
        "singular_snake_case": camel_to_snake(model_name),
        "plural_snake_case": (
            getattr(models, model_name)._meta.verbose_name_plural.replace(" ", "_")
        ),
        "admin_required_to_view": True,
        **overrides,
    }
    for model_name, overrides in CUSTOM_MODEL_VALUES.items()
}
