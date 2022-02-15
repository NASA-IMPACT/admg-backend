from api_app.urls import camel_to_snake
from data_models import models

from . import tables
from . import filters, published_filters

from admin_ui import published_tables


# any custom values for each model are added to this dictionary
# all models must be defined at a minimum with an empty dictionary

# to set the filter, you can either do it directly with the `filter` keyword, or
# you can set a `filter_generator` which takes in a `model_name` in the comprehension

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
    },
    # "GcmdKeyword": {
    #     "display_name": "GCMD Keywords",
    # },
    "DOI": {
        "admin_required_to_view": False,
        "draft_filter": filters.DoiFilter,
        "published_filter": published_filters.DoiFilter,
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
        "draft_filter": filters.DeploymentFilter,
        "published_filter": published_filters.DeploymentFilter,
        "change_view_readonly_fields": ["campaign"],
    },
    "IOP": {
        "admin_required_to_view": False,
        "filter_generator": filters.second_level_campaign_filter,
        "published_filter_generator": published_filters.second_level_campaign_filter,
        "change_view_readonly_fields": ["deployment"],
    },
    "SignificantEvent": {
        "admin_required_to_view": False,
        "filter_generator": filters.second_level_campaign_filter,
        "published_filter_generator": published_filters.second_level_campaign_filter,
        "change_view_readonly_fields": ["deployment"],
    },
    "CollectionPeriod": {
        "display_name": "C-D-P-I",
        "admin_required_to_view": False,
        "draft_filter": filters.CollectionPeriodFilter,
        "published_filter": published_filters.CollectionPeriodFilter,
        "change_view_readonly_fields": ["deployment"],
    },
    "Website": {
        "admin_required_to_view": False,
        "draft_filter": filters.WebsiteFilter,
        "published_filter": published_filters.WebsiteFilter,
    },
    "WebsiteType": {},
}

# defaults are assigned to each model in this comprehension, and then overwritten by the above dictionary
MODEL_CONFIG_MAP = {
    model_name: {
        "draft_filter": overrides.get("filter_generator", filters.GenericDraftFilter)(
            model_name
        ),
        "published_filter": overrides.get("published_filter_generator", published_filters.GenericPublishedListFilter)(
            model_name
        ),
        "model": getattr(models, model_name),
        "published_table": getattr(published_tables, f"{model_name}PublishedTable"),
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
