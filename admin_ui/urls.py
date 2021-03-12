from django.conf import settings
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("deploy-admin/", views.deploy_admin, name="deploy-admin"),
    path("", views.ChangeSummaryView.as_view(), name="summary"),
    path("drafts", views.ChangeListView.as_view(), name="change-list"),
    path("platforms", views.PlatformListView.as_view(), name="platform-list"),
    path("drafts/<uuid:pk>", views.ChangeDetailView.as_view(), name="change-detail"),
    path("drafts/add/<str:model>", views.ChangeCreateView.as_view(), name="change-add"),
    path("drafts/edit/<uuid:pk>", views.ChangeUpdateView.as_view(), name="change-form"),
    # TODO: Consider restraining transitions via Regex or something else
    path(
        "drafts/edit/<uuid:pk>/transitions/<str:transition>",
        views.ChangeTransition.as_view(),
        name="change-transitions",
    ),
    path("tbd", views.to_be_developed, name="to-be-developed"),
]
