from django.contrib import admin


class LimitedInfoAdmin(admin.ModelAdmin):
    list_display = ("short_name", "long_name")
