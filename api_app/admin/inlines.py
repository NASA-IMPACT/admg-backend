from django.contrib.contenttypes.admin import GenericTabularInline

from ..models import Change, PENDING_CODE, IN_PROGRESS_CODE


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

    # TODO: Only let author or superuser change
    # https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin.has_change_permission
    # https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#inlinemodeladmin-options
    # Is it possible to determine change permissions on a per inline basis?


class PendingChangeInline(BaseChangeInline):
    verbose_name_plural = "Pending Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=PENDING_CODE)


class InProgressChangeInline(BaseChangeInline):
    verbose_name_plural = "In Progress Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=IN_PROGRESS_CODE)

