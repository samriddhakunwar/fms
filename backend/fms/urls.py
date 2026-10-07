from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

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

urlpatterns = [
    path("", lambda request: redirect("schema-swagger-ui"), name="root"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.api_urls")),
    path("api/", include("accounts.users_urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("employees.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("reports.urls")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]
