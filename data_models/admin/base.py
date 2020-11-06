from data_models.admin.campaign import LimitedInfoAdmin
from django.contrib import admin

from data_models.models import (
    PlatformType,
    NasaMission,
    InstrumentType,
    HomeBase,
    FocusArea,
    Season,
    Repository,
    MeasurementRegion,
    GeographicalRegion,
    GeophysicalConcept,
    PartnerOrg,
    GcmdProject,
    GcmdInstrument,
    GcmdPlatform,
    GcmdPhenomena,
    DOI,
    Platform,
    Instrument,
    Deployment,
    IOP,
    SignificantEvent,
    CollectionPeriod,
    Alias,
    Image,
)


admin.site.register(PlatformType)
admin.site.register(NasaMission)
admin.site.register(InstrumentType)
admin.site.register(HomeBase)
admin.site.register(FocusArea)
admin.site.register(Season)
admin.site.register(Repository)
admin.site.register(MeasurementRegion)
admin.site.register(GeographicalRegion)
admin.site.register(GeophysicalConcept)
admin.site.register(PartnerOrg)
admin.site.register(GcmdProject)
admin.site.register(GcmdInstrument)
admin.site.register(GcmdPlatform)
admin.site.register(GcmdPhenomena)
admin.site.register(DOI)
admin.site.register(Platform, LimitedInfoAdmin)
admin.site.register(Instrument, LimitedInfoAdmin)
admin.site.register(Deployment, LimitedInfoAdmin)
admin.site.register(IOP)
admin.site.register(SignificantEvent)
admin.site.register(CollectionPeriod)
admin.site.register(Alias)
admin.site.register(Image)
