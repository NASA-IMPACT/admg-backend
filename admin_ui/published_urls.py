
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import published_views
from .config import MODEL_CONFIG_MAP

list_urls = [
    path(
        f"{MODEL_CONFIG_MAP[item]['url']}/published",
        published_views.GenericListView(item).as_view(),
        name=f"mi-{MODEL_CONFIG_MAP[item]['display_name']}-list-published"
    )
    for item in MODEL_CONFIG_MAP
]


detail_urls = [
    path(
        f"{MODEL_CONFIG_MAP[item]['url']}/published/<uuid:pk>",
        published_views.GenericDetailView(item).as_view(),
        name=f"mi-{MODEL_CONFIG_MAP[item]['display_name']}-detail-published"
    )
    for item in MODEL_CONFIG_MAP
]


edit_urls = [
    path(
        f"{MODEL_CONFIG_MAP[item]['url']}/published/<uuid:pk>/edit",
        published_views.GenericEditView(item).as_view(),
        name=f"mi-{MODEL_CONFIG_MAP[item]['display_name']}-edit-published"
    )
    for item in MODEL_CONFIG_MAP
]


published_urls = list_urls + detail_urls + edit_urls
