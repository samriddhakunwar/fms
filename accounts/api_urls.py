from django.urls import path

from . import api_views

urlpatterns = [
    path("login/", api_views.api_login, name="api_auth_login"),
]
