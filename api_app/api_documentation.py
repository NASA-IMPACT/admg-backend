from drf_yasg import openapi

with open('api_app/api_documentation.md', 'r') as f:
    description = f.read()

api_info = openapi.Info(
    title="ADMG CASEI API Documentation",
    default_version="v1",
    description=description,
    # terms_of_service="https://www.google.com/policies/terms/",
    # contact=openapi.Contact(email="contact@snippets.local"),
    # license=openapi.License(name="BSD License"),
)
