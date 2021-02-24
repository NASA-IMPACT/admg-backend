from admin_ui.admin.actions.doi import fetch_dois
from django.contrib import admin

from data_models import models

from .permissions import EnforcedPermissionsMixin
from .inlines.change import PendingChangeInline, InProgressChangeInline
from .inlines.doi import (
    CampaignDoiInline,
    DoiCampaignInline,
    InstrumentDoiInline,
    DoiInstrumentInline,
    PlatformDoiInline,
    DoiPlatformInline,
    CollectionPeriodDoiInline,
    DoiCollectionPeriodInline,
)

class CampaignWebsiteInline(admin.TabularInline):
    model = models.Campaign.websites.through
    fields = ["website", "priority"]
    ordering = ("priority",)


LIMITED_INFO_LIST_FIELDS = ("short_name", "long_name")

CHANGABLE_INLINES = (PendingChangeInline, InProgressChangeInline)


@admin.register(models.Alias)
@admin.register(models.Image)
class BasicAdmin(admin.ModelAdmin, EnforcedPermissionsMixin):
    ...


@admin.register(models.CollectionPeriod)
class CollectionPeriodAdmin(BasicAdmin):
    inlines = [CollectionPeriodDoiInline]


@admin.register(models.DOI)
class DoiAdmin(BasicAdmin):
    inlines = [
        DoiCampaignInline,
        DoiInstrumentInline,
        DoiPlatformInline,
        DoiCollectionPeriodInline,
    ]


@admin.register(models.PlatformType)
@admin.register(models.MeasurementStyle)
@admin.register(models.MeasurementType)
@admin.register(models.HomeBase)
@admin.register(models.FocusArea)
@admin.register(models.Season)
@admin.register(models.Repository)
@admin.register(models.MeasurementRegion)
@admin.register(models.GeographicalRegion)
@admin.register(models.GeophysicalConcept)
class LimitedInfoAdmin(BasicAdmin):
    list_display = LIMITED_INFO_LIST_FIELDS


@admin.register(models.Campaign)
class CampaignAdmin(BasicAdmin):
    actions = [fetch_dois]
    inlines = CHANGABLE_INLINES + (CampaignDoiInline, )
    list_display = ("short_name", "long_name", "funding_agency")
    list_filter = (
        "ongoing",
        "nasa_led",
        "nasa_missions",
        "focus_areas",
        "seasons",
        "repositories",
        "platform_types",
        "partner_orgs",
        "geophysical_concepts",
    )

    inlines = [CampaignWebsiteInline, ] + ChangeableAdmin.inlines

@admin.register(models.Deployment)
@admin.register(models.PartnerOrg)
class LimitedInfoChangable(BasicAdmin):
    inlines = CHANGABLE_INLINES
    list_display = LIMITED_INFO_LIST_FIELDS


@admin.register(models.Instrument)
class InstrumentAdmin(BasicAdmin):
    actions = [fetch_dois]
    inlines = CHANGABLE_INLINES + (InstrumentDoiInline,)
    list_display = LIMITED_INFO_LIST_FIELDS


@admin.register(models.Platform)
class PlatformAdmin(BasicAdmin):
    actions = [fetch_dois]
    inlines = CHANGABLE_INLINES + (PlatformDoiInline,)
    list_display = LIMITED_INFO_LIST_FIELDS
    list_filter = ("platform_type",)


@admin.register(models.IOP)
@admin.register(models.SignificantEvent)
class ShortNameChangable(BasicAdmin):
    inlines = CHANGABLE_INLINES
    list_display = ("short_name",)


@admin.register(models.PartnerOrg)
class PartnerOrgAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.CampaignWebsite)
class CampaignWebsiteAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ["__str__", "campaign", "priority"]


admin.site.register(models.GcmdProject, EnforcedPermissions)
admin.site.register(models.GcmdInstrument, EnforcedPermissions)
admin.site.register(models.GcmdPlatform, EnforcedPermissions)
admin.site.register(models.GcmdPhenomena, EnforcedPermissions)
admin.site.register(models.DOI, EnforcedPermissions)
admin.site.register(models.CollectionPeriod, EnforcedPermissions)
admin.site.register(models.Alias, EnforcedPermissions)
admin.site.register(models.Image, EnforcedPermissions)
admin.site.register(models.WebsiteType, EnforcedPermissions)
admin.site.register(models.Website, EnforcedPermissions)
