from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin", views.trigger_deploy, name="mi-trigger-deploy"),
    path("", views.SummaryView.as_view(), name="mi-summary"),
    path("campaigns", views.CampaignListView.as_view(), name="mi-campaign-list"),
    path(
        "campaigns/<uuid:pk>",
        views.CampaignDetailView.as_view(),
        name="mi-campaign-detail",
    ),
    path(
        "campaigns/<uuid:pk>/fetch-dois",
        views.FetchDois.as_view(),
        name="mi-fetch-dois",
    ),
    path("platforms", views.PlatformListView.as_view(), name="mi-platform-list"),
    path("instruments", views.InstrumentListView.as_view(), name="mi-instrument-list"),
    path(
        "organizations",
        views.PartnerOrgListView.as_view(),
        name="mi-organization-list",
    ),
    path(
        "drafts/add/<str:model>", views.ChangeCreateView.as_view(), name="mi-change-add"
    ),
    path(
        "drafts/edit/<uuid:pk>",
        views.ChangeUpdateView.as_view(),
        name="mi-change-update",
    ),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="mi-change-transition",
    ),
    path(
        "limitedfields",
        RedirectView.as_view(pattern_name="lf-gcmd-list"),
        name="lf-base",
    ),
    path(
        "limitedfields/gcmd",
        views.LimitedFieldGCMDListView.as_view(),
        name="lf-gcmd-list",
    ),
    path(
        "limitedfields/science",
        views.LimitedFieldScienceListView.as_view(),
        name="lf-science-list",
    ),
    path(
        "limitedfields/measurementplatform",
        views.LimitedFieldMeasurmentPlatformListView.as_view(),
        name="lf-measure-platform-list",
    ),
    path(
        "limitedfields/regionseason",
        views.LimitedFieldRegionSeasonListView.as_view(),
        name="lf-region-season-list",
    ),
    path(
        "limitedfields/website",
        views.LimitedFieldWebsiteListView.as_view(),
        name="lf-website-list",
    ),
    path(
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),
]
