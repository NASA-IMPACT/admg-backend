from django.urls import path

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views.DummyApiView import DummyAPIListCreate, DummyAPIRetrieveUpdateDelete

info = openapi.Info(
    title="Snippets API",
    default_version="v1",
    description="Test description",
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="contact@snippets.local"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("dummy/", DummyAPIListCreate.as_view(), name="dummy_list_create"),
    path("dummy/<int:pk>", DummyAPIRetrieveUpdateDelete.as_view(), name="dummy_retrieve_update_delete"),
    # path(
    #     "docs/",
    #     schema_view.with_ui("redoc", cache_timeout=0),
    #     name="schema-swagger-ui"
    # ),
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui"
    ),
]
