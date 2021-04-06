from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("deploy-admin/", views.deploy_admin, name="deploy-admin"),
    path("", views.SummaryView.as_view(), name="mi-summary"),
    path("campaigns", views.CampaignListView.as_view(), name="mi-campaign-list"),
    path("platforms", views.PlatformListView.as_view(), name="mi-platform-list"),
    path("instruments", views.InstrumentListView.as_view(), name="mi-instrument-list"),
    path(
        "organizations",
        views.PartnerOrgListView.as_view(),
        name="mi-organization-list",
    ),
    path(
        "campaigns/<uuid:pk>",
        views.CampaignDetailView.as_view(),
        name="mi-campaign-detail",
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
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),
]
