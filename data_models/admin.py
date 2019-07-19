from django.contrib import admin
from .models import (PlatformType,
                    AircraftType, 
                    InstrumentType, 
                    HomeBase, 
                    FocusArea, 
                    Season, 
                    Repository, 
                    Campaign, 
                    Instrument, 
                    Platform, 
                    Flight, 
                    Deployment)

admin.site.register(PlatformType)
admin.site.register(AircraftType)
admin.site.register(InstrumentType)
admin.site.register(HomeBase)
admin.site.register(FocusArea)
admin.site.register(Season)
admin.site.register(Repository)
admin.site.register(Campaign)
admin.site.register(Instrument)
admin.site.register(Platform)
admin.site.register(Flight)
admin.site.register(Deployment)