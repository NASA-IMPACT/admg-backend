from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView

from . import views
from .views import v2

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin", views.trigger_deploy, name="trigger-deploy"),
    path("", views.SummaryView.as_view(), name="summary"),
    # path("campaigns/<uuid:pk>/details", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path(
        "v2/<str:model>/<uuid:canonical_uuid>/details",
        v2.CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path("campaigns/<uuid:pk>/doi-fetch", views.DoiFetchView.as_view(), name="doi-fetch"),
    path("campaigns/<uuid:pk>/doi-approval", views.DoiApprovalView.as_view(), name="doi-approval"),
    path(
        "v2/<str:model>/<uuid:pk>/doi-approval",
        views.DoiApprovalView.as_view(),
        name="doi-approval",
    ),
    # NOTE: For 'model' arg of URL, snake_case of model class name is expected
    path("drafts/<str:model>", views.ChangeListView.as_view(), name="change-list"),
    path("drafts/<str:model>/add", views.ChangeCreateView.as_view(), name="change-add"),
    path("drafts/edit/<uuid:pk>", views.ChangeUpdateView.as_view(), name="change-update"),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="change-transition",
    ),
    path("gcmd_list/draft", views.GcmdSyncListView.as_view(), name="gcmd-list"),
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
    path('v2/<str:model>', v2.CanonicalRecordList.as_view(), name="canonical-list"),
    # Helper route to redirect user to appropriate view without prior knowledge of record's status (ie if it's been published). If published, return redirect to `/<uuid:canonical_uuid>/published`. Otherwise, redirect to `/<uuid:canonical_uuid>/edit`.
    path(
        'v2/<str:model>/<uuid:canonical_uuid>/<uuid:draft_uuid>',
        v2.redirect_helper,
        name="canonical-redirect",
    ),
    # Read-only view the published record for this concept. Render `400` response if record is not yet published.
    path(
        'v2/<str:model>/<uuid:canonical_uuid>/published/<uuid:draft_uuid>',
        v2.CanonicalRecordPublished.as_view(),
        name="canonical-published-detail",
    ),
    # Update for latest published draft.
    path(
        'v2/<str:model>/<uuid:canonical_uuid>/edit/<uuid:draft_uuid>',
        v2.CanonicalDraftEdit.as_view(),
        name="canonical-draft-edit",
    ),
    # same view as edit but view only for historical
    path(
        'v2/<str:model>/<uuid:canonical_uuid>/history/<uuid:draft_uuid>',
        v2.HistoryDetailView.as_view(),
        name="historical-detail",
    ),
    # List all `Change` records for a given concept. Ordered by date created, descending.
    path(
        "v2/<str:model>/<uuid:canonical_uuid>/history",
        v2.ChangeHistoryList.as_view(),
        name="change-history",
    ),
    # Create a new change draft from existing published record
    path(
        "v2/<str:model>/<uuid:canonical_uuid>/create-update",
        v2.CreateUpdateView.as_view(),
        name="create-update",
    ),
    # Create new Change view
    path(
        "v2/<str:model>/create",
        v2.CreateInitialView.as_view(),
        name="create-initial",
    ),
]
