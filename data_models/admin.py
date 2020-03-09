from django.contrib import admin

from .models import (
    PlatformType,
    AircraftType,
    InstrumentType,
    HomeBase,
    FocusArea,
    Season,
    Repository,
    MeasurementRegion,
    MeasurementKeyword,
    GeographicalRegion,
    PartnerOrg,
    GcmdPhenomena,
    GcmdProject,
    GcmdPlatform,
    GcmdInstrument,
    Campaign,
    Platform,
    Instrument,
    Deployment,
    IopSe,
    Flight
)

admin.site.register(PlatformType)
admin.site.register(AircraftType)
admin.site.register(InstrumentType)
admin.site.register(HomeBase)
admin.site.register(FocusArea)
admin.site.register(Season)
admin.site.register(Repository)
admin.site.register(MeasurementRegion)
admin.site.register(MeasurementKeyword)
admin.site.register(GeographicalRegion)
admin.site.register(PartnerOrg)
admin.site.register(GcmdPhenomena)
admin.site.register(GcmdProject)
admin.site.register(GcmdPlatform)
admin.site.register(GcmdInstrument)
admin.site.register(Campaign)
admin.site.register(Platform)
admin.site.register(Instrument)
admin.site.register(Deployment)
admin.site.register(IopSe)
admin.site.register(Flight)
