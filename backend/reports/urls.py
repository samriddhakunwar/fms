from django.urls import path

from . import views

urlpatterns = [
    path("reports/sales/", views.sales_report, name="report_sales"),
    path(
        "reports/sales/history/",
        views.sales_report_history,
        name="report_sales_history",
    ),
]
