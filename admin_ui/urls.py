from django.contrib import admin
from django.urls import path

from .views import ChangeDetailView, ChangeListView

urlpatterns = [
    path("", admin.site.urls),
    path("changes/", ChangeListView.as_view(), name="change-list"),
    path("changes/<uuid:uuid>", ChangeDetailView.as_view(), name="change-detail"),
]
