from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("deploy-admin/", views.deploy_admin, name="deploy-admin"),
    path("", views.ChangeSummaryView.as_view(), name="summary"),
    path("drafts", views.ChangeListView.as_view(), name="change-list"),
    path("platforms", views.PlatformListView.as_view(), name="platform-list"),
    path("instruments", views.InstrumentListView.as_view(), name="instrument-list"),
    path("organizations", views.PartnerOrgListView.as_view(), name="organization-list"),
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
    path("drafts/<uuid:pk>", views.ChangeDetailView.as_view(), name="change-detail"),
    path("drafts/add/<str:model>", views.ChangeCreateView.as_view(), name="change-add"),
    path("drafts/edit/<uuid:pk>", views.ChangeUpdateView.as_view(), name="change-form"),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="change-transition",
    ),
    path("tbd", views.to_be_developed, name="to-be-developed"),
]
