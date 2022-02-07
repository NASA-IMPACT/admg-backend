from django.contrib import admin

from data_models import models

LIMITED_INFO_LIST_FIELDS = ("short_name", "long_name")

CHANGABLE_INLINES = (InProgressInline, InReviewInline, InAdminReviewInline)


@admin.register(models.Alias)
@admin.register(models.CollectionPeriod)
@admin.register(models.DOI)
@admin.register(models.GcmdInstrument)
@admin.register(models.GcmdPhenomena)
@admin.register(models.GcmdPlatform)
@admin.register(models.GcmdProject)
@admin.register(models.Image)
@admin.register(models.Website)
@admin.register(models.WebsiteType)
class BasicAdmin(admin.ModelAdmin):
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

@admin.register(models.Deployment)
@admin.register(models.FocusArea)
@admin.register(models.GeographicalRegion)
@admin.register(models.GeophysicalConcept)
@admin.register(models.HomeBase)
@admin.register(models.Instrument)
@admin.register(models.MeasurementRegion)
@admin.register(models.MeasurementStyle)
@admin.register(models.MeasurementType)
@admin.register(models.PartnerOrg)
@admin.register(models.PlatformType)
@admin.register(models.Repository)
@admin.register(models.Season)
class LimitedInfoAdmin(BasicAdmin):
    list_display = ("short_name", "long_name")


@admin.register(models.Campaign)
class CampaignAdmin(BasicAdmin):
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
    inlines = (CampaignDoiInline,) + CHANGABLE_INLINES


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
    list_filter = ("platform_type",)


@admin.register(models.IOP)
@admin.register(models.SignificantEvent)
class ShortNameChangable(BasicAdmin):
    list_display = ("short_name",)
