from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# ---------------------------------------------------------------------------
# Swagger / OpenAPI schema view
# ---------------------------------------------------------------------------
schema_view = get_schema_view(
    openapi.Info(
        title="Factory Management System API",
        default_version="v1",
        description="REST API for the Factory Management System.",
        contact=openapi.Contact(email="admin@factory.local"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------
urlpatterns = [
    # Root → redirect to login
    path("", lambda request: redirect("accounts:login"), name="root"),

    # HTML application
    path("", include("accounts.urls")),

    # Django admin panel
    path("admin/", admin.site.urls),

    # API endpoints
    path("api/auth/", include("accounts.api_urls")),

    # Swagger UI
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),

    # ReDoc
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),

    # Raw OpenAPI JSON (useful for importing into Postman, etc.)
    path(
        "api/",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
]
