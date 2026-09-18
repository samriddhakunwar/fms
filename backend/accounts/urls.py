from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # HTML views
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-dashboard/",     views.admin_dashboard,     name="admin_dashboard"),
    path("inventory-dashboard/", views.inventory_dashboard, name="inventory_dashboard"),
    path("employee-dashboard/",  views.employee_dashboard,  name="employee_dashboard"),
]
