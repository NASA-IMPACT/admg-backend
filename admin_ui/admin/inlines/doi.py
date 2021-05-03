from api_app.models import Change
from data_models.models import DOI
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


def get_admin_url(obj, field="uuid"):
    url = reverse(
        "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
        args=[getattr(obj, field)],
    )
    return u'<a href="%s">%s</a>' % (url, obj)


class BaseDoiInline(admin.TabularInline):
    extra = 0
    show_change_link = True
    fields = ("_doi",)
    readonly_fields = ("_doi",)

    def _doi(self, obj):
        return mark_safe(get_admin_url(obj.doi))

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj):
        return False


class CampaignDoiInline(BaseDoiInline):
    """
    Inline to demonstrate DOIs associated with a given Campaign
    """

    model = DOI.campaigns.through


class DraftCampaignDoiInline(CampaignDoiInline):
    model = Change

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def formfield_for_dbfield(self, db_field, request, **kwargs):

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class DoiCampaignInline(CampaignDoiInline):
    fields = ("_campaign",)
    readonly_fields = ("_campaign",)

    def _campaign(self, obj):
        return mark_safe(get_admin_url(obj.campaign))


class InstrumentDoiInline(BaseDoiInline):
    """
    Inline to demonstrate DOIs associated with a given Instrument
    """

    model = DOI.instruments.through


class DoiInstrumentInline(InstrumentDoiInline):
    fields = ("_instrument",)
    readonly_fields = ("_instrument",)

    def _instrument(self, obj):
        return mark_safe(get_admin_url(obj.instrument))


class PlatformDoiInline(BaseDoiInline):
    """
    Inline to demonstrate DOIs associated with a given Platform
    """

    model = DOI.platforms.through


class DoiPlatformInline(PlatformDoiInline):
    """
    Inline to demonstrate Platforms associated with a given DOI
    """

    fields = ("_platform",)
    readonly_fields = ("_platform",)

    def _platform(self, obj):
        return mark_safe(get_admin_url(obj.platform))


class CollectionPeriodDoiInline(BaseDoiInline):
    """
    Inline to demonstrate DOIs associated with a given CollectionPeriod
    """

    model = DOI.collection_periods.through


class DoiCollectionPeriodInline(CollectionPeriodDoiInline):
    fields = ("_collection_period",)
    readonly_fields = ("_collection_period",)

    def _collection_period(self, obj):
        return mark_safe(get_admin_url(obj.collection_period))
