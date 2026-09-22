from django.urls import path

from . import views

urlpatterns = [
    path("reports/sales/", views.sales_report, name="report_sales"),
]
