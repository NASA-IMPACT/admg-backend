from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("", admin.site.urls),
    path("deploy-admin/", views.deploy_admin, name="deploy-admin"),
    path("drafts", views.ChangeListView.as_view(), name="change-list"),
    path("drafts/<uuid:pk>", views.ChangeDetailView.as_view(), name="change-detail"),
    path("drafts/add/<str:model>", views.ChangeCreateView.as_view(), name="change-add"),
    path("drafts/edit/<uuid:pk>", views.ChangeUpdateView.as_view(), name="change-form"),
    path("tbd", views.to_be_developed, name="to-be-developed"),
]
