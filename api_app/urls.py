from django.urls import path

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views.change_view import (
    ChangeListView,
    ChangeListUpdateView,
    ChangeApproveRejectView,
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

urlpatterns = [
    path(
        "platform_type",
        GenericCreateGetAllView("PlatformType"),
        name="PlatformType_create_getall"
    ),
    path(
        "platform_type/<str:uuid>",
        GenericPutPatchDeleteView("PlatformType"),
        name="PlatformType_put_delete"
    ),
    
    path(
        "aircraft_type",
        GenericCreateGetAllView("AircraftType"),
        name="AircraftType_create_getall"
    ),
    path(
        "aircraft_type/<str:uuid>",
        GenericPutPatchDeleteView("AircraftType"),
        name="AircraftType_put_delete"
    ),

    path(
        "instrument_type",
        GenericCreateGetAllView("InstrumentType"),
        name="InstrumentType_create_getall"
    ),
    path(
        "instrument_type/<str:uuid>",
        GenericPutPatchDeleteView("InstrumentType"),
        name="InstrumentType_put_delete"
    ),

    path(
        "home_base",
        GenericCreateGetAllView("HomeBase"),
        name="HomeBase_create_getall"
    ),
    path(
        "home_base/<str:uuid>",
        GenericPutPatchDeleteView("HomeBase"),
        name="HomeBase_put_delete"
    ),

    path(
        "focus_area",
        GenericCreateGetAllView("FocusArea"),
        name="FocusArea_create_getall"
    ),
    path(
        "focus_area/<str:uuid>",
        GenericPutPatchDeleteView("FocusArea"),
        name="FocusArea_put_delete"
    ),

    path(
        "season",
        GenericCreateGetAllView("Season"),
        name="Season_create_getall"
    ),
    path(
        "season/<str:uuid>",
        GenericPutPatchDeleteView("Season"),
        name="Season_put_delete"
    ),

    path(
        "repository",
        GenericCreateGetAllView("Repository"),
        name="Repository_create_getall"
    ),
    path(
        "repository/<str:uuid>",
        GenericPutPatchDeleteView("Repository"),
        name="Repository_put_delete"
    ),

    path(
        "measurement_region",
        GenericCreateGetAllView("MeasurementRegion"),
        name="MeasurementRegion_create_getall"
    ),
    path(
        "measurement_region/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementRegion"),
        name="MeasurementRegion_put_delete"
    ),

    path(
        "measurement_keyword",
        GenericCreateGetAllView("MeasurementKeyword"),
        name="MeasurementKeyword_create_getall"
    ),
    path(
        "measurement_keyword/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementKeyword"),
        name="MeasurementKeyword_put_delete"
    ),

    path(
        "geographical_region",
        GenericCreateGetAllView("GeographicalRegion"),
        name="GeographicalRegion_create_getall"
    ),
    path(
        "geographical_region/<str:uuid>",
        GenericPutPatchDeleteView("GeographicalRegion"),
        name="GeographicalRegion_put_delete"
    ),

    path(
        "geophysical_concepts",
        GenericCreateGetAllView("GeophysicalConcepts"),
        name="GeophysicalConcepts_create_getall"
    ),
    path(
        "geophysical_concepts/<str:uuid>",
        GenericPutPatchDeleteView("GeophysicalConcepts"),
        name="GeophysicalConcepts_put_delete"
    ),

    path(
        "gcmd_phenomena",
        GenericCreateGetAllView("GcmdPhenomena"),
        name="GcmdPhenomena_create_getall"
    ),
    path(
        "gcmd_phenomena/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPhenomena"),
        name="GcmdPhenomena_put_delete"
    ),

    path(
        "gcmd_project",
        GenericCreateGetAllView("GcmdProject"),
        name="GcmdProject_create_getall"
    ),
    path(
        "gcmd_project/<str:uuid>",
        GenericPutPatchDeleteView("GcmdProject"),
        name="GcmdProject_put_delete"
    ),

    path(
        "gcmd_platform",
        GenericCreateGetAllView("GcmdPlatform"),
        name="GcmdPlatform_create_getall"
    ),
    path(
        "gcmd_platform/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPlatform"),
        name="GcmdPlatform_put_delete"
    ),

    path(
        "gcmd_instrument",
        GenericCreateGetAllView("GcmdInstrument"),
        name="GcmdInstrument_create_getall"
    ),
    path(
        "gcmd_instrument/<str:uuid>",
        GenericPutPatchDeleteView("GcmdInstrument"),
        name="GcmdInstrument_put_delete"
    ),

    path(
        "partner_org",
        GenericCreateGetAllView("PartnerOrg"),
        name="PartnerOrg_create_getall"
    ),
    path(
        "partner_org/<str:uuid>",
        GenericPutPatchDeleteView("PartnerOrg"),
        name="PartnerOrg_put_delete"
    ),

    path(
        "event_type",
        GenericCreateGetAllView("EventType"),
        name="EventType_create_getall"
    ),
    path(
        "event_type/<str:uuid>",
        GenericPutPatchDeleteView("EventType"),
        name="EventType_put_delete"
    ),

    path(
        "campaign",
        GenericCreateGetAllView("Campaign"),
        name="Campaign_create_getall"
    ),
    path(
        "campaign/<str:uuid>",
        GenericPutPatchDeleteView("Campaign"),
        name="Campaign_put_delete"
    ),

    path(
        "platform",
        GenericCreateGetAllView("Platform"),
        name="Platform_create_getall"
    ),
    path(
        "platform/<str:uuid>",
        GenericPutPatchDeleteView("Platform"),
        name="Platform_put_delete"
    ),

    path(
        "instrument",
        GenericCreateGetAllView("Instrument"),
        name="Instrument_create_getall"
    ),
    path(
        "instrument/<str:uuid>",
        GenericPutPatchDeleteView("Instrument"),
        name="Instrument_put_delete"
    ),

    path(
        "deployment",
        GenericCreateGetAllView("Deployment"),
        name="Deployment_create_getall"
    ),
    path(
        "deployment/<str:uuid>",
        GenericPutPatchDeleteView("Deployment"),
        name="Deployment_put_delete"
    ),

    path(
        "iop_se",
        GenericCreateGetAllView("IopSe"),
        name="IopSe_create_getall"
    ),
    path(
        "iop_se/<str:uuid>",
        GenericPutPatchDeleteView("IopSe"),
        name="IopSe_put_delete"
    ),

    path(
        "flight",
        GenericCreateGetAllView("Flight"),
        name="Flight_create_getall"
    ),
    path(
        "flight/<str:uuid>",
        GenericPutPatchDeleteView("Flight"),
        name="Flight_put_delete"
    ),

    path(
        "pending_change",
        ChangeListView.as_view(),
        name="pending_change_list"
    ),
    path(
        "pending_change/<str: uuid>",
        ChangeListUpdateView.as_view(),
        name="pending_change_list"
    ),
    path(
        f"pending_change/<str: uuid>/{APPROVE}",
        ChangeApproveRejectView(APPROVE),
        name="pending_change_list"
    ),
    path(
        f"pending_change/<str: uuid>/{REJECT}",
        ChangeApproveRejectView(REJECT),
        name="pending_change_list"
    ),


    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui"
    ),
]
