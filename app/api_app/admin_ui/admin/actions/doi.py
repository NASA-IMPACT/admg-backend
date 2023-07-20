from django.contrib import messages


def fetch_dois(modeladmin, request, queryset):
    messages.add_message(
        request, messages.INFO, f"Scheduled DOI fetch operations for {queryset.count()} models"
    )


fetch_dois.short_description = "Fetch DOIs for selected"
