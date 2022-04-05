from django.urls import path

from . import published_views

published_urls = [
    path(
        f"published/<str:model>", published_views.GenericListView.as_view(), name="published-list"
    ),
    path(
        f"published/<str:model>/<uuid:pk>",
        published_views.GenericDetailView.as_view(),
        name="published-detail",
    ),
    path(
        f"published/<str:model>/<uuid:pk>/edit",
        published_views.GenericEditView.as_view(),
        name="published-edit",
    ),
    path(
        f"published/<str:model>/<uuid:pk>/delete",
        published_views.GenericDeleteView.as_view(),
        name="published-delete",
    ),
]
