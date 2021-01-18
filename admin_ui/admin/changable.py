from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.contenttypes.admin import GenericTabularInline

from api_app.models import Change, PENDING_CODE, IN_PROGRESS_CODE


class BaseChangeInline(GenericTabularInline):
    model = Change
    ct_fk_field = "model_instance_uuid"

    extra = 0

    def has_add_permission(self, request, obj):
        # Changes may not be manually added. They should on be created by saving
        # a model
        return False

    def has_change_permission(self, request, obj):
        # Changes may not be manually added. They should on be created by saving
        # a model
        return False


class PendingChangeInline(BaseChangeInline):
    verbose_name_plural = "Pending Changes"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=PENDING_CODE)


class InProgressChangeInline(BaseChangeInline):
    verbose_name_plural = "In Progress Changes"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=IN_PROGRESS_CODE)


class ChangableAdmin(admin.ModelAdmin):
    inlines = [PendingChangeInline, InProgressChangeInline]
