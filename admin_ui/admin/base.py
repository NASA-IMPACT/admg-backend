from admg_webapp.users.models import ADMIN_CODE
from django.contrib import admin


class EnforcedPermissions(admin.ModelAdmin):
    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return self.is_admin(request)

    def has_add_permission(self, request, obj=None):
        return self.is_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self.is_admin(request)

    @staticmethod
    def is_admin(request):
        if not hasattr(request.user, 'role'):
            # AnonymousUsers won't have role property
            return False
        return request.user.role == ADMIN_CODE
