from django.contrib import admin

from data_models.models import Platform
from api_app.admin import ChangeAdmin
from .base import LimitedInfoAdmin


class PlatformAdmin(LimitedInfoAdmin, ChangeAdmin):
    # list_display = (*LimitedInfoAdmin.list_display, "funding_agency")
    list_filter = (
        "platform_type",
    )


admin.site.register(Platform, PlatformAdmin)
