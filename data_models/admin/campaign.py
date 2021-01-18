from django.contrib import admin

from data_models.models import Campaign
from admin_ui.admin.changable import ChangableAdmin
from .base import LimitedInfoAdmin


class CampaignAdmin(LimitedInfoAdmin, ChangableAdmin):
    list_display = (*LimitedInfoAdmin.list_display, "funding_agency")
    list_filter = (
        "ongoing",
        "nasa_led",
        "nasa_missions",
        "focus_areas",
        "seasons",
        "repositories",
        "platform_types",
        "partner_orgs",
        "gcmd_projects",
        "geophysical_concepts",
    )


admin.site.register(Campaign, CampaignAdmin)
