from django.contrib import admin

from data_models.models import Platform
from admin_ui.admin.changable import ChangableAdmin
from .base import LimitedInfoAdmin


class PlatformAdmin(LimitedInfoAdmin, ChangableAdmin):
    list_filter = ("platform_type",)


admin.site.register(Platform, PlatformAdmin)
