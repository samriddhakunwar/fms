from django.contrib import admin

from .forms import SaleItemAdminForm
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    form = SaleItemAdminForm
    extra = 1

    # Columns rendered inside the inline table
    fields = (
        "product",
        "quantity",
        "unit_price",
        "subtotal",  # Read-only — computed by SaleItem.save()
    )

    readonly_fields = ("subtotal",)

    raw_id_fields = ("product",)


# Sale admin
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]

    # List view
    list_display = (
        "invoice_number",
        "sold_to",       # Customer the invoice was issued to
        "order",
        "total_amount",
        "sale_date",
    )

    list_display_links = ("invoice_number",)

    list_filter = ("sale_date",)   # Date-based sidebar filter

    search_fields = (
        "invoice_number",   # Direct match on invoice number
        "sold_to",          # Customer / company name
    )

    # Most recent sales first
    ordering = ("-sale_date",)

    # Date drill-down navigation bar
    date_hierarchy = "sale_date"

    # Detail (add / change) view
    readonly_fields = ("invoice_number", "sale_date", "total_amount")

    raw_id_fields = ("order",)

    fieldsets = (
        (
            "Invoice Header",
            {
                "fields": (
                    "invoice_number",
                    "sold_to",
                    "order",
                    "sale_date",
                ),
            },
        ),
        (
            "Totals",
            {
                "fields": ("total_amount",),
                "description": (
                    "Total amount is computed from line items and is read-only here."
                ),
            },
        ),
    )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    """Standalone admin for individual SaleItem records."""

    # List view
    list_display = (
        "sale",        # Invoice this item belongs to
        "product",     # Renders via Product.__str__
        "quantity",
        "unit_price",
        "subtotal",    # Stored value; auto-computed on save
    )

    list_display_links = ("sale", "product")

    list_filter = (
        "sale__sale_date",
        "product",
    )

    search_fields = (
        "sale__invoice_number",    # Search by invoice number
        "product__product_name",   # Search by product name
        "product__sku",            # Search by SKU
    )

    ordering = ("-sale__sale_date", "id")

    # Detail (add / change) view
    form = SaleItemAdminForm

    readonly_fields = ("subtotal",)

    raw_id_fields = ("sale", "product")

    fieldsets = (
        (
            "Line Item",
            {
                "fields": (
                    "sale",
                    "product",
                    "quantity",
                    "unit_price",
                    "subtotal",
                ),
            },
        ),
    )
