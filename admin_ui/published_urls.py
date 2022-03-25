from django.urls import path

from . import published_views
from data_models.model_config import MODEL_CONFIG_MAP

published_urls = [
    *[
        route
        for model_name, model_config in MODEL_CONFIG_MAP.items()
        for route in [
            # publish urls
            path(
                f"{model_config['plural_snake_case']}/published",
                published_views.GenericListView(model_name).as_view(),
                name=f"{model_config['singular_snake_case']}-list-published",
            ),
            # detail urls
            path(
                f"{model_config['plural_snake_case']}/published/<uuid:pk>",
                published_views.GenericDetailView(model_name).as_view(),
                name=f"{model_config['singular_snake_case']}-detail-published",
            ),
            # edit urls
            path(
                f"{model_config['plural_snake_case']}/published/<uuid:pk>/edit",
                published_views.GenericEditView(model_name).as_view(),
                name=f"{model_config['singular_snake_case']}-edit-published",
            ),
            # delete urls
            path(
                f"{model_config['plural_snake_case']}/published/<uuid:pk>/delete",
                published_views.GenericDeleteView(model_name).as_view(),
                name=f"{model_config['singular_snake_case']}-delete-published",
            ),
        ]
    ]
]
