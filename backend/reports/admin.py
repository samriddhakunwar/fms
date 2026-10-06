from django.contrib import admin

from .models import SalesReport


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    """Log of generated sales reports; written by the report endpoint."""

    list_display = (
        "generated_at",
        "admin",
        "manager",
        "start_date",
        "end_date",
        "sales_count",
        "items_sold",
        "total_revenue",
    )
    list_select_related = ("admin__user", "manager__user")
    list_filter = ("generated_at",)
    search_fields = ("admin__user__username", "manager__user__username")
    ordering = ("-generated_at", "-id")
    date_hierarchy = "generated_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
