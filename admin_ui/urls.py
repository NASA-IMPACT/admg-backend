from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin", views.trigger_deploy, name="trigger-deploy"),
    path("", views.SummaryView.as_view(), name="summary"),
    path("campaigns/<uuid:pk>/details", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path("campaigns/<uuid:pk>/doi-fetch", views.DoiFetchView.as_view(), name="doi-fetch"),
    path("campaigns/<uuid:pk>/doi-approval", views.DoiApprovalView.as_view(), name="doi-approval"),
    # NOTE: For 'model' arg of URL, snake_case of model class name is expected
    path("drafts/<str:model>", views.ChangeListView.as_view(), name="change-list"),
    path("drafts/<str:model>/add", views.ChangeCreateView.as_view(), name="change-add"),
    path("drafts/edit/<uuid:pk>", views.ChangeUpdateView.as_view(), name="change-update"),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="change-transition",
    ),
    path(
        "gcmd_list/draft",
        views.GcmdSyncListView.as_view(),
        name="gcmd-list",
    ),
    path("drafts/edit/gcmd/<uuid:pk>", views.ChangeGcmdUpdateView.as_view(), name="change-gcmd"),
    path(
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),
    path("published/<str:model>", views.PublishedListView.as_view(), name="published-list"),
    path(
        "published/<str:model>/<uuid:pk>",
        views.PublishedDetailView.as_view(),
        name="published-detail",
    ),
    path(
        "published/<str:model>/<uuid:pk>/edit",
        views.PublishedEditView.as_view(),
        name="published-edit",
    ),
    path(
        "published/<str:model>/<uuid:pk>/delete",
        views.PublishedDeleteView.as_view(),
        name="published-delete",
    ),
]
