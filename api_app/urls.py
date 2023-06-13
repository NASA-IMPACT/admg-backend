import re

from django.urls import path
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .api_documentation import api_info
from .views.change_view import (
    ApprovalLogListView,
    ChangeClaimView,
    ChangeListUpdateView,
    ChangeListView,
    ChangePublishView,
    ChangeRejectView,
    ChangeReviewView,
    ChangeSubmitView,
    ChangeUnclaimView,
    ChangeValidationView,
)
from .views.generic_views import GenericCreateGetAllView, GenericPutPatchDeleteView
from .views.image_view import ImageListCreateAPIView, ImageRetrieveDestroyAPIView
from .views.validation_view import JsonValidationView
from .views.unpublished_view import UnpublishedListCreateAPIView

info = api_info

schema_view = get_schema_view(public=True, permission_classes=(permissions.AllowAny,))

urls = [
    "PlatformType",
    "MeasurementType",
    "MeasurementStyle",
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
    "GcmdPhenomenon",
    "DOI",
    "Campaign",
    "Platform",
    "Instrument",
    "Deployment",
    "IOP",
    "SignificantEvent",
    "CollectionPeriod",
    "Website",
    "WebsiteType",
]

urlpatterns = []


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


for url in urls:
    snake_case_url = camel_to_snake(url)
    urlpatterns.append(
        path(snake_case_url, GenericCreateGetAllView(url), name=f"{url}_create_getall")
    )
    urlpatterns.append(
        path(
            f"{snake_case_url}/<str:uuid>", GenericPutPatchDeleteView(url), name=f"{url}_put_delete"
        )
    )


urlpatterns += [
    path("approval_log", ApprovalLogListView.as_view(), name="approval_log_list"),
    path("change_request", ChangeListView.as_view(), name="change_request_list"),
    path("unpublished_drafts", UnpublishedListCreateAPIView.as_view(), name="unpublished"),
    path(
        "change_request/<str:uuid>",
        ChangeListUpdateView.as_view(),
        name="change_request_list_update",
    ),
    path(
        "change_request/<str:uuid>/validate",
        ChangeValidationView.as_view(),
        name="change_request_validate",
    ),
    path(
        "change_request/<str:uuid>/submit", ChangeSubmitView.as_view(), name="change_request_submit"
    ),
    path(
        "change_request/<str:uuid>/review", ChangeReviewView.as_view(), name="change_request_review"
    ),
    path(
        "change_request/<str:uuid>/publish",
        ChangePublishView.as_view(),
        name="change_request_publish",
    ),
    path(
        "change_request/<str:uuid>/reject", ChangeRejectView.as_view(), name="change_request_reject"
    ),
    path("change_request/<str:uuid>/claim", ChangeClaimView.as_view(), name="change_request_claim"),
    path(
        "change_request/<str:uuid>/unclaim",
        ChangeUnclaimView.as_view(),
        name="change_request_unclaim",
    ),
    path("image", ImageListCreateAPIView.as_view(), name="image_list_create"),
    path("image/<str:uuid>", ImageRetrieveDestroyAPIView.as_view(), name="image_retrieve_destroy"),
    path("validate_json", JsonValidationView.as_view(), name="validate_json"),
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
]
