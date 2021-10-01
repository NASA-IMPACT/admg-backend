
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import published_views
from .config import MODEL_CONFIG_MAP

list_urls = [
    path(
        f"{MODEL_CONFIG_MAP[model]['plural_snake_case']}/published",
        published_views.GenericListView(model).as_view(),
        name=f"{MODEL_CONFIG_MAP[model]['singular_snake_case']}-list-published"
    )
    for model in MODEL_CONFIG_MAP
]


detail_urls = [
    path(
        f"{MODEL_CONFIG_MAP[model]['plural_snake_case']}/published/<uuid:pk>",
        published_views.GenericDetailView(model).as_view(),
        name=f"{MODEL_CONFIG_MAP[model]['singular_snake_case']}-detail-published"
    )
    for model in MODEL_CONFIG_MAP
]


edit_urls = [
    path(
        f"{MODEL_CONFIG_MAP[model]['plural_snake_case']}/published/<uuid:pk>/edit",
        published_views.GenericEditView(model).as_view(),
        name=f"{MODEL_CONFIG_MAP[model]['singular_snake_case']}-edit-published"
    )
    for model in MODEL_CONFIG_MAP
]


diff_url = [
    path(
        "published/<uuid:pk>/diff",
        published_views.DiffView.as_view(),
        name="change-diff"
    )
]


published_urls = list_urls + detail_urls + edit_urls + diff_url
