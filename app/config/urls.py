from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views import defaults as default_views
from api_app.utils import CustomTokenView

urlpatterns = [
    # Admin
    path("", include("admin_ui.urls")),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    # User management
    path("users/", include("admg_webapp.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("api/", include("api_app.urls")),
    path("authenticate/token/", CustomTokenView.as_view(), name="token"),
    path("authenticate/", include("oauth2_provider.urls"), name="oauth2_provider"),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
