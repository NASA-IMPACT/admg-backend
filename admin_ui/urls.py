from django.contrib import admin
from django.urls import path

from .views import deploy_admin

urlpatterns = [
    path("", admin.site.urls),
    path("deploy-admin/", deploy_admin, name="deploy-admin"),
]
