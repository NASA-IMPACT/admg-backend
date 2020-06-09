import re
from django.urls import path

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views.change_view import (
    ChangeListView,
    ChangeListUpdateView,
    ChangeApproveRejectView,
    ChangePushView,
    APPROVE,
    REJECT
)

from .views.generic_views import GenericCreateGetAllView, GenericPutPatchDeleteView

info = openapi.Info(
    title="ADMG API",
    default_version="v1",
    description="API endpoints for ADMG application",
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="contact@snippets.local"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urls = [
    "PlatformType",
    "NasaMission",
    "InstrumentType",
    "HomeBase",
    "FocusArea",
    "Season",
    "Repository",
    "MeasurementRegion",
    "GeographicalRegion",
    "GeophysicalConcept",
    "PartnerOrg",
    "Alias",
    "GcmdProject",
    "GcmdInstrument",
    "GcmdPlatform",
    "GcmdPhenomena",
    "Campaign",
    "Platform",
    "Instrument",
    "Deployment",
    "IOP",
    "SignificantEvent",
    "CollectionPeriod",
    "ExternalMetadata",
]

urlpatterns = []


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


for url in urls:
    snake_case_url = camel_to_snake(url)
    urlpatterns.append(
        path(
            snake_case_url,
            GenericCreateGetAllView(url),
            name=f"{url}_create_getall"
        ),
    )
    urlpatterns.append(
        path(
            f"{snake_case_url}/<str:uuid>",
            GenericPutPatchDeleteView(url),
            name=f"{url}_put_delete"
        ),
    )


urlpatterns += [
    path(
        "change_request",
        ChangeListView.as_view(),
        name="change_request_list"
    ),
    path(
        "change_request/<str:uuid>",
        ChangeListUpdateView.as_view(),
        name="change_request_list_update"
    ),
    path(
        f"change_request/<str:uuid>/{APPROVE}",
        ChangeApproveRejectView(APPROVE),
        name="change_request_approve"
    ),
    path(
        f"change_request/<str:uuid>/{REJECT}",
        ChangeApproveRejectView(REJECT),
        name="change_request_reject"
    ),
    path(
        f"change_request/<str:uuid>/push",
        ChangePushView.as_view(),
        name="change_request_push"
    ),

    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui"
    ),
]
