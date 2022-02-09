from django.contrib import admin

from api_app.models import Change


class ModelToBeChangedFilter(admin.SimpleListFilter):
    title = "data type"
    parameter_name = "content_type_id"

    def lookups(self, request, model_admin):
        return [("all", "Show all")] + [
            (c.content_type_id, c.model_name)
            for c in Change.objects.distinct("content_type").select_related("content_type")
        ]

    def queryset(self, request, queryset):
        content_type_id = self.value()
        return queryset.filter(content_type_id=content_type_id) if content_type_id else queryset


def short_name(obj):
    return obj.update.get("short_name")


short_name.short_description = "Short Name"


class ChangeAdmin(admin.ModelAdmin):
    SUBMODEL_FIELDNAME_PREFIX = "submodel__"

    search_fields = ("uuid", "update__uuid", "update__short_name", "update__long_name")
    list_display = (
        short_name,
        "model_name",
        "action",
        "status",
    )
    list_filter = ("status", "action", ModelToBeChangedFilter)
    readonly_fields = ("previous", "uuid", "model_instance_uuid")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("content_type")


admin.site.register(Change, ChangeAdmin)
