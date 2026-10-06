from django.contrib import admin

from fms.actor import role_fields

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
        "created_by_admin",
        "created_by_manager",
    )
    list_select_related = ("created_by_admin__user", "created_by_manager__user")
    list_display_links = ("order_number",)
    list_filter = ("status", "order_date")
    search_fields = ("order_number", "customer_name")
    ordering = ("-order_date",)
    date_hierarchy = "order_date"

    readonly_fields = (
        "order_number",
        "order_date",
        "total_amount",
        "created_by_admin",
        "created_by_manager",
    )

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
                    "created_by_admin",
                    "created_by_manager",
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

    def save_model(self, request, obj, form, change):
        if not change:
            for field, profile in role_fields(request.user, "created_by_").items():
                setattr(obj, field, profile)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_total()
