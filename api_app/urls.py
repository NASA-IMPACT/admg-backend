from django.urls import path

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import GenericCreateGetAllView, GenericPutPatchDeleteView

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
        "PlatformType",
        GenericCreateGetAllView("PlatformType").as_view(),
        name="PlatformType_create_getall"
    ),

    path(
        "PlatformType/<str:uuid>",
        GenericPutPatchDeleteView("PlatformType").as_view(),
        name="PlatformType_put_delete"
    ),

    path(
        "AircraftType",
        GenericCreateGetAllView("AircraftType").as_view(),
        name="AircraftType_create_getall"
    ),

    path(
        "AircraftType/<str:uuid>",
        GenericPutPatchDeleteView("AircraftType").as_view(),
        name="AircraftType_put_delete"
    ),

    path(
        "InstrumentType",
        GenericCreateGetAllView("InstrumentType").as_view(),
        name="InstrumentType_create_getall"
    ),

    path(
        "InstrumentType/<str:uuid>",
        GenericPutPatchDeleteView("InstrumentType").as_view(),
        name="InstrumentType_put_delete"
    ),

    path(
        "HomeBase",
        GenericCreateGetAllView("HomeBase").as_view(),
        name="HomeBase_create_getall"
    ),

    path(
        "HomeBase/<str:uuid>",
        GenericPutPatchDeleteView("HomeBase").as_view(),
        name="HomeBase_put_delete"
    ),

    path(
        "FocusArea",
        GenericCreateGetAllView("FocusArea").as_view(),
        name="FocusArea_create_getall"
    ),

    path(
        "FocusArea/<str:uuid>",
        GenericPutPatchDeleteView("FocusArea").as_view(),
        name="FocusArea_put_delete"
    ),

    path(
        "Season",
        GenericCreateGetAllView("Season").as_view(),
        name="Season_create_getall"
    ),

    path(
        "Season/<str:uuid>",
        GenericPutPatchDeleteView("Season").as_view(),
        name="Season_put_delete"
    ),

    path(
        "Repository",
        GenericCreateGetAllView("Repository").as_view(),
        name="Repository_create_getall"
    ),

    path(
        "Repository/<str:uuid>",
        GenericPutPatchDeleteView("Repository").as_view(),
        name="Repository_put_delete"
    ),

    path(
        "MeasurementRegion",
        GenericCreateGetAllView("MeasurementRegion").as_view(),
        name="MeasurementRegion_create_getall"
    ),

    path(
        "MeasurementRegion/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementRegion").as_view(),
        name="MeasurementRegion_put_delete"
    ),

    path(
        "MeasurementKeyword",
        GenericCreateGetAllView("MeasurementKeyword").as_view(),
        name="MeasurementKeyword_create_getall"
    ),

    path(
        "MeasurementKeyword/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementKeyword").as_view(),
        name="MeasurementKeyword_put_delete"
    ),

    path(
        "GeographicalRegion",
        GenericCreateGetAllView("GeographicalRegion").as_view(),
        name="GeographicalRegion_create_getall"
    ),

    path(
        "GeographicalRegion/<str:uuid>",
        GenericPutPatchDeleteView("GeographicalRegion").as_view(),
        name="GeographicalRegion_put_delete"
    ),

    path(
        "GeophysicalConcepts",
        GenericCreateGetAllView("GeophysicalConcepts").as_view(),
        name="GeophysicalConcepts_create_getall"
    ),

    path(
        "GeophysicalConcepts/<str:uuid>",
        GenericPutPatchDeleteView("GeophysicalConcepts").as_view(),
        name="GeophysicalConcepts_put_delete"
    ),

    path(
        "GcmdPhenomena",
        GenericCreateGetAllView("GcmdPhenomena").as_view(),
        name="GcmdPhenomena_create_getall"
    ),

    path(
        "GcmdPhenomena/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPhenomena").as_view(),
        name="GcmdPhenomena_put_delete"
    ),

    path(
        "GcmdProject",
        GenericCreateGetAllView("GcmdProject").as_view(),
        name="GcmdProject_create_getall"
    ),

    path(
        "GcmdProject/<str:uuid>",
        GenericPutPatchDeleteView("GcmdProject").as_view(),
        name="GcmdProject_put_delete"
    ),

    path(
        "GcmdPlatform",
        GenericCreateGetAllView("GcmdPlatform").as_view(),
        name="GcmdPlatform_create_getall"
    ),

    path(
        "GcmdPlatform/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPlatform").as_view(),
        name="GcmdPlatform_put_delete"
    ),

    path(
        "GcmdInstrument",
        GenericCreateGetAllView("GcmdInstrument").as_view(),
        name="GcmdInstrument_create_getall"
    ),

    path(
        "GcmdInstrument/<str:uuid>",
        GenericPutPatchDeleteView("GcmdInstrument").as_view(),
        name="GcmdInstrument_put_delete"
    ),

    path(
        "PartnerOrg",
        GenericCreateGetAllView("PartnerOrg").as_view(),
        name="PartnerOrg_create_getall"
    ),

    path(
        "PartnerOrg/<str:uuid>",
        GenericPutPatchDeleteView("PartnerOrg").as_view(),
        name="PartnerOrg_put_delete"
    ),

    path(
        "EventType",
        GenericCreateGetAllView("EventType").as_view(),
        name="EventType_create_getall"
    ),

    path(
        "EventType/<str:uuid>",
        GenericPutPatchDeleteView("EventType").as_view(),
        name="EventType_put_delete"
    ),

    path(
        "Campaign",
        GenericCreateGetAllView("Campaign").as_view(),
        name="Campaign_create_getall"
    ),

    path(
        "Campaign/<str:uuid>",
        GenericPutPatchDeleteView("Campaign").as_view(),
        name="Campaign_put_delete"
    ),

    path(
        "Platform",
        GenericCreateGetAllView("Platform").as_view(),
        name="Platform_create_getall"
    ),

    path(
        "Platform/<str:uuid>",
        GenericPutPatchDeleteView("Platform").as_view(),
        name="Platform_put_delete"
    ),

    path(
        "Instrument",
        GenericCreateGetAllView("Instrument").as_view(),
        name="Instrument_create_getall"
    ),

    path(
        "Instrument/<str:uuid>",
        GenericPutPatchDeleteView("Instrument").as_view(),
        name="Instrument_put_delete"
    ),

    path(
        "Deployment",
        GenericCreateGetAllView("Deployment").as_view(),
        name="Deployment_create_getall"
    ),

    path(
        "Deployment/<str:uuid>",
        GenericPutPatchDeleteView("Deployment").as_view(),
        name="Deployment_put_delete"
    ),

    path(
        "IopSe",
        GenericCreateGetAllView("IopSe").as_view(),
        name="IopSe_create_getall"
    ),

    path(
        "IopSe/<str:uuid>",
        GenericPutPatchDeleteView("IopSe").as_view(),
        name="IopSe_put_delete"
    ),

    path(
        "Flight",
        GenericCreateGetAllView("Flight").as_view(),
        name="Flight_create_getall"
    ),

    path(
        "Flight/<str:uuid>",
        GenericPutPatchDeleteView("Flight").as_view(),
        name="Flight_put_delete"
    ),

    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui"
    ),
]
