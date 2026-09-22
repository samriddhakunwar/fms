"""
orders/admin.py
===============
Admin configuration for Order and its line items.

Line items are edited inline on the order, mirroring the Sale admin, so a
whole order is one screen. The order number and total are read-only: the
number is generated on creation and the total is computed from the lines
(recalculated in save_related once the inline rows have been written).
"""

from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("product", "quantity", "unit_price", "subtotal")
    readonly_fields = ("subtotal",)
    raw_id_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

    list_display = (
        "order_number",
        "customer_name",
        "status",
        "total_amount",
        "order_date",
        "expected_delivery_date",
    )
    list_display_links = ("order_number",)
    list_filter = ("status", "order_date")
    search_fields = ("order_number", "customer_name")
    ordering = ("-order_date",)
    date_hierarchy = "order_date"

    readonly_fields = ("order_number", "order_date", "total_amount")

    fieldsets = (
        (
            "Order Header",
            {
                "fields": (
                    "order_number",
                    "customer_name",
                    "status",
                    "order_date",
                    "expected_delivery_date",
                    "notes",
                )
            },
        ),
        (
            "Totals",
            {
                "fields": ("total_amount",),
                "description": (
                    "Computed from the line items; edit the lines to change it."
                ),
            },
        ),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_total()
