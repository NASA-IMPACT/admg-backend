
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import published_views

list_urls = [
    path(
        "campaigns/published",
        published_views.CampaignListView.as_view(),
        name="mi-campaign-list-published"
    ),
    path("platforms/published", published_views.PlatformListView.as_view(), name="mi-platform-list-published"),
    path(
        "instruments/published",
        published_views.InstrumentListView.as_view(),
        name="mi-instrument-list-published"
    ),
    path(
        "websites/published",
        published_views.WebsiteListView.as_view(),
        name="website-list-published",
    ),
    path(
        "aliases/published",
        published_views.AliasListView.as_view(),
        name="alias-list-published",
    ),
    path(
        "limitedfields/gcmd/published",
        published_views.LimitedFieldGCMDListView.as_view(),
        name="lf-gcmd-list-published",
    ),
    path(
        "limitedfields/science/published",
        published_views.LimitedFieldScienceListView.as_view(),
        name="lf-science-list-published",
    ),
    path(
        "limitedfields/measurementplatform/published",
        published_views.LimitedFieldMeasurmentPlatformListView.as_view(),
        name="lf-measure-platform-list-published",
    ),
    path(
        "limitedfields/regionseason/published",
        published_views.LimitedFieldRegionSeasonListView.as_view(),
        name="lf-region-season-list-published",
    ),
    path(
        "limitedfields/website/published",
        published_views.LimitedFieldWebsiteListView.as_view(),
        name="lf-website-list-published",
    )
]

detail_urls = []


published_urls = list_urls + detail_urls
