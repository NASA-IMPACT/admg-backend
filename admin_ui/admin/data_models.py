from django.contrib import admin

from data_models import models

from .changable import ChangableAdmin


@admin.register(models.PlatformType)
class PlatformTypeAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementStyle)
class MeasurementStyleAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementType)
class MeasurementTypeAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.HomeBase)
class HomeBaseAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.MeasurementRegion)
class MeasurementRegionAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.GeographicalRegion)
class GeographicalRegionAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.GeophysicalConcept)
class GeophysicalConceptAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Campaign)
class CampaignAdmin(ChangableAdmin):
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


@admin.register(models.Instrument)
class InstrumentAdmin(ChangableAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Platform)
class PlatformAdmin(ChangableAdmin):
    list_display = ("short_name", "long_name")
    list_filter = ("platform_type",)


@admin.register(models.Deployment)
class DeploymentAdmin(ChangableAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.IOP)
class IOPAdmin(ChangableAdmin):
    list_display = ("short_name",)


@admin.register(models.SignificantEvent)
class SignificantEventAdmin(ChangableAdmin):
    list_display = ("short_name",)


@admin.register(models.PartnerOrg)
class PartnerOrgAdmin(ChangableAdmin):
    list_display = ("short_name", "long_name")


admin.site.register(models.GcmdProject)
admin.site.register(models.GcmdInstrument)
admin.site.register(models.GcmdPlatform)
admin.site.register(models.GcmdPhenomena)
admin.site.register(models.DOI)
admin.site.register(models.CollectionPeriod)
admin.site.register(models.Alias)
admin.site.register(models.Image)
