from django.contrib import admin

from data_models import models

from .base import EnforcedPermissions
from .changeable import ChangeableAdmin

class CampaignWebsiteInline(admin.TabularInline):
    model = models.Campaign.websites.through
    fields = ["website", "priority"]
    ordering = ("priority",)


@admin.register(models.PlatformType)
class PlatformTypeAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementStyle)
class MeasurementStyleAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementType)
class MeasurementTypeAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.HomeBase)
class HomeBaseAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.FocusArea)
class FocusAreaAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.Season)
class SeasonAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.Repository)
class RepositoryAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementRegion)
class MeasurementRegionAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.GeographicalRegion)
class GeographicalRegionAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.GeophysicalConcept)
class GeophysicalConceptAdmin(EnforcedPermissions):
    list_display = ("short_name", "long_name")


@admin.register(models.Campaign)
class CampaignAdmin(EnforcedPermissions, ChangeableAdmin):
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
        "gcmd_projects",
        "geophysical_concepts",
    )

    inlines = [CampaignWebsiteInline, ] + ChangeableAdmin.inlines

@admin.register(models.Instrument)
class InstrumentAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Platform)
class PlatformAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ("short_name", "long_name")
    list_filter = ("platform_type",)


@admin.register(models.Deployment)
class DeploymentAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.IOP)
class IOPAdmin(EnforcedPermissions, ChangeableAdmin):
    list_display = ("short_name",)


@admin.register(models.SignificantEvent)
class SignificantEventAdmin(EnforcedPermissions, ChangeableAdmin):
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
