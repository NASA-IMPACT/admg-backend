from data_models.models import PlatformType
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import views
from .published_urls import published_urls

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin",
        views.trigger_deploy,
        name="trigger-deploy"
    ),
    path("",
        views.SummaryView.as_view(),
        name="summary"
    ),
    path("campaigns/drafts",
        views.CampaignListView.as_view(),
        name="campaign-list"
    ),
    path(
        "campaigns/<uuid:pk>",
        views.CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path(
        "campaigns/<uuid:pk>/doi-fetch",
        views.DoiFetchView.as_view(),
        name="doi-fetch",
    ),
    path(
        "campaigns/<uuid:pk>/doi-approval",
        views.DoiApprovalView.as_view(),
        name="doi-approval",
    ),  
    path(
        "platforms/drafts",
        views.PlatformListView.as_view(),
        name="platform-list"
    ),
    path(
        "instruments/drafts",
        views.InstrumentListView.as_view(),
        name="instrument-list"
    ),
    path(
        "organizations/drafts",
        views.PartnerOrgListView.as_view(),
        name="organization-list",
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
        "drafts/add/<str:model>",
        views.ChangeCreateView.as_view(),
        name="change-add"
    ),
    path(
        "drafts/edit/<uuid:pk>",
        views.ChangeUpdateView.as_view(),
        name="change-update",
    ),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="change-transition",
    ),
    path(
        "gcmd_projects/draft",
        views.GcmdProjectListView.as_view(),
        name="gcmd_project-list"
    ),
    path(
        "gcmd_instruments/draft",
        views.GcmdInstrumentListView.as_view(),
        name="gcmd_instrument-list"
    ),
    path(
        "gcmd_platforms/draft",
        views.GcmdPlatformListView.as_view(),
        name="gcmd_platform-list"
    ),
    path(
        "gcmd_phenomena/draft",
        views.GcmdPhenomenaListView.as_view(),
        name="gcmd_phenomena-list"
    ),
    
    path(
        "limitedfields/science/drafts",
        views.LimitedFieldScienceListView.as_view(),
        name="science-list",
    ),
    
    path(
        "limitedfields/measurementplatform/drafts",
        views.LimitedFieldMeasurmentPlatformListView.as_view(),
        name="measure-platform-list",
    ),
    
    path(
        "limitedfields/regionseason/drafts",
        views.LimitedFieldRegionSeasonListView.as_view(),
        name="region-season-list",
    ),
    
    path(
        "limitedfields/website/drafts",
        views.LimitedFieldWebsiteListView.as_view(),
        name="website-list",
    ),
    path(
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),
]

urlpatterns = urlpatterns + published_urls
