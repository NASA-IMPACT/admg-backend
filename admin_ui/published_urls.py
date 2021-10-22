from django.urls import path

from . import published_views
from .config import MODEL_CONFIG_MAP

published_urls = [
    *[
        route
        for model, config in MODEL_CONFIG_MAP.items()
        for route in [
            path(
                f"{config['plural_snake_case']}/published",
                published_views.GenericListView(model).as_view(),
                name=f"{config['singular_snake_case']}-list-published",
            ),
            path(
                f"{config['plural_snake_case']}/published/<uuid:pk>",
                published_views.GenericDetailView(model).as_view(),
                name=f"{config['singular_snake_case']}-detail-published",
            ),
            path(
                f"{config['plural_snake_case']}/published/<uuid:pk>/edit",
                published_views.GenericEditView(model).as_view(),
                name=f"{config['singular_snake_case']}-edit-published",
            ),
        ]
    ],
    path(
        "published/<uuid:pk>/diff",
        published_views.DiffView.as_view(),
        name="change-diff",
    ),
]
