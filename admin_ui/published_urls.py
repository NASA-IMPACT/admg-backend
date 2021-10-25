from django.urls import path

from . import published_views
from .config import MODEL_CONFIG_MAP

published_urls = [
    *[
        route
        for model, config in MODEL_CONFIG_MAP.items()
        for route in [
            # publish urls
            path(
                f"{config['plural_snake_case']}/published",
                published_views.GenericListView(model).as_view(),
                name=f"{config['singular_snake_case']}-list-published",
            ),
            # detail urls
            path(
                f"{config['plural_snake_case']}/published/<uuid:pk>",
                published_views.GenericDetailView(model).as_view(),
                name=f"{config['singular_snake_case']}-detail-published",
            ),
            # edit urls
            path(
                f"{config['plural_snake_case']}/published/<uuid:pk>/edit",
                published_views.GenericEditView(model).as_view(),
                name=f"{config['singular_snake_case']}-edit-published",
            ),
            # delete urls
            path(
                f"{MODEL_CONFIG_MAP[model]['plural_snake_case']}/published/<uuid:pk>/delete",
                published_views.GenericDeleteView(model).as_view(),
                name=f"{MODEL_CONFIG_MAP[model]['singular_snake_case']}-delete-published",
            ),
        ]
    ],
    path(
        "published/<uuid:pk>/diff",
        published_views.DiffView.as_view(),
        name="change-diff",
    ),
]
