from django.contrib import admin
from django.urls import path

from .views import deploy_admin, ChangeDetailView, ChangeUpdateView, ChangeCreateView

urlpatterns = [
    path("", admin.site.urls),
    path("deploy-admin/", deploy_admin, name="deploy-admin"),
    path("changes/<uuid:pk>", ChangeDetailView.as_view(), name="change-detail"),
    path("changes/add/<str:model>", ChangeCreateView.as_view(), name="change-add"),
    path("changes/edit/<uuid:pk>", ChangeUpdateView.as_view(), name="change-form"),
]
