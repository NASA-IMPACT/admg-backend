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
        "platform_type",
        GenericCreateGetAllView("PlatformType").as_view(),
        name="PlatformType_create_getall"
    ),

    path(
        "platform_type/<str:uuid>",
        GenericPutPatchDeleteView("PlatformType").as_view(),
        name="PlatformType_put_delete"
    ),

    path(
        "aircraft_type",
        GenericCreateGetAllView("AircraftType").as_view(),
        name="AircraftType_create_getall"
    ),

    path(
        "aircraft_type/<str:uuid>",
        GenericPutPatchDeleteView("AircraftType").as_view(),
        name="AircraftType_put_delete"
    ),

    path(
        "instrument_type",
        GenericCreateGetAllView("InstrumentType").as_view(),
        name="InstrumentType_create_getall"
    ),

    path(
        "instrument_type/<str:uuid>",
        GenericPutPatchDeleteView("InstrumentType").as_view(),
        name="InstrumentType_put_delete"
    ),

    path(
        "home_base",
        GenericCreateGetAllView("HomeBase").as_view(),
        name="HomeBase_create_getall"
    ),

    path(
        "home_base/<str:uuid>",
        GenericPutPatchDeleteView("HomeBase").as_view(),
        name="HomeBase_put_delete"
    ),

    path(
        "focus_area",
        GenericCreateGetAllView("FocusArea").as_view(),
        name="FocusArea_create_getall"
    ),

    path(
        "focus_area/<str:uuid>",
        GenericPutPatchDeleteView("FocusArea").as_view(),
        name="FocusArea_put_delete"
    ),

    path(
        "season",
        GenericCreateGetAllView("Season").as_view(),
        name="Season_create_getall"
    ),

    path(
        "season/<str:uuid>",
        GenericPutPatchDeleteView("Season").as_view(),
        name="Season_put_delete"
    ),

    path(
        "repository",
        GenericCreateGetAllView("Repository").as_view(),
        name="Repository_create_getall"
    ),

    path(
        "repository/<str:uuid>",
        GenericPutPatchDeleteView("Repository").as_view(),
        name="Repository_put_delete"
    ),

    path(
        "measurement_region",
        GenericCreateGetAllView("MeasurementRegion").as_view(),
        name="MeasurementRegion_create_getall"
    ),

    path(
        "measurement_region/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementRegion").as_view(),
        name="MeasurementRegion_put_delete"
    ),

    path(
        "measurement_keyword",
        GenericCreateGetAllView("MeasurementKeyword").as_view(),
        name="MeasurementKeyword_create_getall"
    ),

    path(
        "measurement_keyword/<str:uuid>",
        GenericPutPatchDeleteView("MeasurementKeyword").as_view(),
        name="MeasurementKeyword_put_delete"
    ),

    path(
        "geographical_region",
        GenericCreateGetAllView("GeographicalRegion").as_view(),
        name="GeographicalRegion_create_getall"
    ),

    path(
        "geographical_region/<str:uuid>",
        GenericPutPatchDeleteView("GeographicalRegion").as_view(),
        name="GeographicalRegion_put_delete"
    ),

    path(
        "geophysical_concepts",
        GenericCreateGetAllView("GeophysicalConcepts").as_view(),
        name="GeophysicalConcepts_create_getall"
    ),

    path(
        "geophysical_concepts/<str:uuid>",
        GenericPutPatchDeleteView("GeophysicalConcepts").as_view(),
        name="GeophysicalConcepts_put_delete"
    ),

    path(
        "gcmd_phenomena",
        GenericCreateGetAllView("GcmdPhenomena").as_view(),
        name="GcmdPhenomena_create_getall"
    ),

    path(
        "gcmd_phenomena/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPhenomena").as_view(),
        name="GcmdPhenomena_put_delete"
    ),

    path(
        "gcmd_project",
        GenericCreateGetAllView("GcmdProject").as_view(),
        name="GcmdProject_create_getall"
    ),

    path(
        "gcmd_project/<str:uuid>",
        GenericPutPatchDeleteView("GcmdProject").as_view(),
        name="GcmdProject_put_delete"
    ),

    path(
        "gcmd_platform",
        GenericCreateGetAllView("GcmdPlatform").as_view(),
        name="GcmdPlatform_create_getall"
    ),

    path(
        "gcmd_platform/<str:uuid>",
        GenericPutPatchDeleteView("GcmdPlatform").as_view(),
        name="GcmdPlatform_put_delete"
    ),

    path(
        "gcmd_instrument",
        GenericCreateGetAllView("GcmdInstrument").as_view(),
        name="GcmdInstrument_create_getall"
    ),

    path(
        "gcmd_instrument/<str:uuid>",
        GenericPutPatchDeleteView("GcmdInstrument").as_view(),
        name="GcmdInstrument_put_delete"
    ),

    path(
        "partner_org",
        GenericCreateGetAllView("PartnerOrg").as_view(),
        name="PartnerOrg_create_getall"
    ),

    path(
        "partner_org/<str:uuid>",
        GenericPutPatchDeleteView("PartnerOrg").as_view(),
        name="PartnerOrg_put_delete"
    ),

    path(
        "event_type",
        GenericCreateGetAllView("EventType").as_view(),
        name="EventType_create_getall"
    ),

    path(
        "event_type/<str:uuid>",
        GenericPutPatchDeleteView("EventType").as_view(),
        name="EventType_put_delete"
    ),

    path(
        "campaign",
        GenericCreateGetAllView("Campaign").as_view(),
        name="Campaign_create_getall"
    ),

    path(
        "campaign/<str:uuid>",
        GenericPutPatchDeleteView("Campaign").as_view(),
        name="Campaign_put_delete"
    ),

    path(
        "platform",
        GenericCreateGetAllView("Platform").as_view(),
        name="Platform_create_getall"
    ),

    path(
        "platform/<str:uuid>",
        GenericPutPatchDeleteView("Platform").as_view(),
        name="Platform_put_delete"
    ),

    path(
        "instrument",
        GenericCreateGetAllView("Instrument").as_view(),
        name="Instrument_create_getall"
    ),

    path(
        "instrument/<str:uuid>",
        GenericPutPatchDeleteView("Instrument").as_view(),
        name="Instrument_put_delete"
    ),

    path(
        "deployment",
        GenericCreateGetAllView("Deployment").as_view(),
        name="Deployment_create_getall"
    ),

    path(
        "deployment/<str:uuid>",
        GenericPutPatchDeleteView("Deployment").as_view(),
        name="Deployment_put_delete"
    ),

    path(
        "iop_se",
        GenericCreateGetAllView("IopSe").as_view(),
        name="IopSe_create_getall"
    ),

    path(
        "iop_se/<str:uuid>",
        GenericPutPatchDeleteView("IopSe").as_view(),
        name="IopSe_put_delete"
    ),

    path(
        "flight",
        GenericCreateGetAllView("Flight").as_view(),
        name="Flight_create_getall"
    ),

    path(
        "flight/<str:uuid>",
        GenericPutPatchDeleteView("Flight").as_view(),
        name="Flight_put_delete"
    ),

    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui"
    ),
]
