from admin_ui.config import MODEL_CONFIG_MAP
from data_models.models import PlatformType
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView, RedirectView

from . import views
from .published_urls import published_urls

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Actions
    path("actions/deploy-admin",
        views.trigger_deploy,
        name="trigger-deploy"
    ),
    path("",
        views.SummaryView.as_view(),
        name="summary"
    ),
    path(
        "campaigns/<uuid:pk>",
        views.CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path(
        "campaigns/<uuid:pk>/doi-fetch",
        views.DoiFetchView.as_view(),
        name="doi-fetch",
    ),
    path(
        "campaigns/<uuid:pk>/doi-approval",
        views.DoiApprovalView.as_view(),
        name="doi-approval",
    ),  
    path(
        "drafts/add/<str:model>",
        views.ChangeCreateView.as_view(),
        name="change-add"
    ),
    path(
        "drafts/edit/<uuid:pk>",
        views.ChangeUpdateView.as_view(),
        name="change-update",
    ),
    path(
        "drafts/edit/<uuid:pk>/transition",
        views.ChangeTransition.as_view(),
        name="change-transition",
    ),   
    path(
        "tbd",
        TemplateView.as_view(template_name="api_app/to_be_developed.html"),
        name="to-be-developed",
    ),

]

from admin_ui.views import generate_base_list_view

# limited has short, long


auto_url_keys = [
    "PlatformType", #parent
    "MeasurementType", #parent
    "MeasurementStyle", #parent
    "HomeBase", #location
    "FocusArea", #url
    "Season", # none
    "Repository", # gcmd_uuid
    "MeasurementRegion", # example, gcmd_uuid
    "GeographicalRegion", # example, gcmd_uuid
    "GeophysicalConcept", # example, gcmd_uuid
    "PartnerOrg", # website
    "Alias", # NO INHERITEANCE, short_name, how to do model?
    "GcmdProject",
    "GcmdInstrument",
    "GcmdPlatform",
    "GcmdPhenomena",
    # "DOI", # no url?
    "Campaign",
    "Platform",
    "Instrument",
    # "Deployment", # no url?
    # "IOP", # no url?
    # "SignificantEvent", # no url?
    # "CollectionPeriod", # no url? 
    "Website", #NO INHERITANCE, title, url, website_type
    "WebsiteType", # none
    # "CampaignWebsite",
]

draft_list_urls = [
    path(
        f"{MODEL_CONFIG_MAP[model]['plural_snake_case']}/draft",
        generate_base_list_view(model),
        name=f"{MODEL_CONFIG_MAP[model]['singular_snake_case']}-list-draft"
    )
    for model in auto_url_keys
]


urlpatterns = urlpatterns + published_urls + draft_list_urls
