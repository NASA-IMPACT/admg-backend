from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import views
from .published_urls import published_urls

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin", views.trigger_deploy, name="mi-trigger-deploy"),
    path("", views.SummaryView.as_view(), name="mi-summary"),
    path("campaigns/drafts", views.CampaignListView.as_view(), name="mi-campaign-list"),
    path(
        "campaigns/<uuid:pk>",
        views.CampaignDetailView.as_view(),
        name="mi-campaign-detail",
    ),
    path(
        "campaigns/<uuid:pk>/doi-fetch",
        views.DoiFetchView.as_view(),
        name="mi-doi-fetch",
    ),
    path(
        "campaigns/<uuid:pk>/doi-approval",
        views.DoiApprovalView.as_view(),
        name="mi-doi-approval",
    ),

    
    path("platforms/drafts", views.PlatformListView.as_view(), name="mi-platform-list"),
    
    path("instruments/drafts", views.InstrumentListView.as_view(), name="mi-instrument-list"),

    path(
        "organizations/published",
        published_views.PartnerOrgListView.as_view(),
        name="mi-organization-list-published",
    ),
    path(
        "organizations/drafts",
        views.PartnerOrgListView.as_view(),
        name="mi-organization-list",
    ),
    
    path(
        "websites/drafts",
        views.WebsiteListView.as_view(),
        name="website-list",
    ),
    
    path(
        "aliases",
        views.AliasListView.as_view(),
        name="alias-list",
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
        "limitedfields/gcmd/draft",
        views.LimitedFieldGCMDListView.as_view(),
        name="lf-gcmd-list",
    ),
    
    path(
        "limitedfields/science/drafts",
        views.LimitedFieldScienceListView.as_view(),
        name="lf-science-list",
    ),
    
    path(
        "limitedfields/measurementplatform/drafts",
        views.LimitedFieldMeasurmentPlatformListView.as_view(),
        name="lf-measure-platform-list",
    ),
    
    path(
        "limitedfields/regionseason/drafts",
        views.LimitedFieldRegionSeasonListView.as_view(),
        name="lf-region-season-list",
    ),
    
    path(
        "limitedfields/website/drafts",
        views.LimitedFieldWebsiteListView.as_view(),
        name="lf-website-list",
    ),
    path(
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),
]

urlpatterns = urlpatterns + published_urls
