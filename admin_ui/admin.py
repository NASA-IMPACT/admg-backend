from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType

from api_app.models import Change, UPDATE, CREATE, PATCH, PENDING_CODE, IN_PROGRESS_CODE


class BaseChangesInline(GenericTabularInline):
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


class PendingChangesInline(BaseChangesInline):
    verbose_name_plural = "Pending Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=PENDING_CODE)


class InProgressChangesInline(BaseChangesInline):
    verbose_name_plural = "In Progress Changes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=IN_PROGRESS_CODE)


class ChangeAdmin(admin.ModelAdmin):
    inlines = [PendingChangesInline, InProgressChangesInline]

    def save_model(self, request, obj, form, change):
        if request.user.is_superuser or not form.changed_data:
            return super().save_model(request, obj, form, change)
        # if action == CREATE:
        #     # the user should still be able to add in few partial fields
        #     serializer = self.get_serializer(data=request.data, partial=True)
        #     serializer.is_valid(raise_exception=True)
        # elif action == UPDATE:
        #     partial = action == PATCH or kwargs.pop('partial', False)
        #     instance = self.get_object()
        #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
        #     serializer.is_valid(raise_exception=True)

        # TODO:
        # serializer_class = getattr(sz, f"{self.model_name}Serializer")
        # instance = model.objects.get(uuid=self.model_instance_uuid)
        # if self.action == UPDATE:
        #     serializer = serializer_class(instance)

        return Change.objects.create(
            content_type=ContentType.objects.get_for_model(obj),
            update={k: form.data[k] for k in form.changed_data},
            model_instance_uuid=obj.uuid,
            action=UPDATE if change else CREATE,
            user=request.user,
        )


# class ModelOptions(admin.ModelAdmin):
#     fieldsets = (
#         ('', {
#             'fields': ('title', 'subtitle', 'slug', 'pub_date', 'status',),
#         }),
#         ('Flags', {
#             'classes': ('grp-collapse grp-closed',),
#             'fields' : ('flag_front', 'flag_sticky', 'flag_allow_comments', 'flag_comments_closed',),
#         }),
#         ('Tags', {
#             'classes': ('grp-collapse grp-open',),
#             'fields' : ('tags',),
#         }),
#     )
