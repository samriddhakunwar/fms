from django.urls import path

from . import api_views

urlpatterns = [
    path("login/", api_views.api_login, name="api_auth_login"),
    path("logout/", api_views.api_logout, name="api_auth_logout"),
    path("me/", api_views.api_current_user, name="api_auth_me"),
    path("csrf/", api_views.api_csrf, name="api_auth_csrf"),
]
