from django.contrib import admin
from django.urls import path

from .views import deploy_admin, CampaignGroupView, MyFormView

urlpatterns = [
    path("", admin.site.urls),
    path("deploy-admin/", deploy_admin, name="deploy-admin"),
    # path("changes/<uuid:uuid>", CampaignGroupView.as_view(), name="change-detail"),
    path("changes/<uuid:uuid>", MyFormView.as_view(), name="change-detail"),
]
