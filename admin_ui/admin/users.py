from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.contrib.admin import TabularInline
from allauth.account.models import EmailAddress

User = get_user_model()


class EmailAddressInline(TabularInline):
    model = EmailAddress
    extra = 0


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        ("User", {"fields": ("name", "role")}),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "name", "is_superuser", "role"]
    search_fields = ["name"]
    inlines = [EmailAddressInline]
