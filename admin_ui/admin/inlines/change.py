from django.utils.translation import gettext as _
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.admin import ModelAdmin

from api_app.models import Change, IN_PROGRESS_CODE, IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE


class BaseChangeInline(GenericTabularInline):
    model = Change
    ct_fk_field = "model_instance_uuid"
    classes = ('collapse',)

    extra = 0

    def has_add_permission(self, request, obj):
        # Changes may not be manually added. They should be created by saving
        # a model
        return False

    def has_change_permission(self, request, obj):
        # Changes may not be manually added. They should be created by saving
        # a model
        return False


class InProgressInline(BaseChangeInline):
    verbose_name_plural = "In Progress"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=IN_PROGRESS_CODE)


class InReviewInline(BaseChangeInline):
    verbose_name_plural = "In Review"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=IN_REVIEW_CODE)


class InAdminReviewInline(BaseChangeInline):
    verbose_name_plural = "In Admin Review"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=IN_ADMIN_REVIEW_CODE)
