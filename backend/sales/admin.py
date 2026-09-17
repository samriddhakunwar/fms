"""
sales/admin.py
==============
Admin configuration for the Sale and SaleItem models.

Key design decisions
---------------------
• SaleItemInline — line items are managed on the Sale change form as a
  tabular inline.  This gives a single-screen view of an entire invoice
  (header + line items) rather than forcing the admin to navigate across
  two separate pages.

• subtotal is auto-computed by SaleItem.save() so it is shown as read-only
  in the inline.  Likewise, total_amount on Sale is kept as readonly to
  prevent manual tampering; it should be recalculated by application logic.

• sale_date and invoice_number on Sale are readonly after creation to
  preserve invoice integrity.
"""

from django.contrib import admin

from .models import Sale, SaleItem


# ---------------------------------------------------------------------------
# SaleItem inline  — shown embedded in the Sale change form
# ---------------------------------------------------------------------------

class SaleItemInline(admin.TabularInline):
    """
    Displays all line items of an invoice directly on the Sale change form.

    TabularInline renders each SaleItem as a compact row in a table, which
    is ideal for invoice-style data with multiple columns.
    """

    model = SaleItem
    extra = 1  # Always show one blank row for adding a new item

    # Columns rendered inside the inline table
    fields = (
        "product",
        "quantity",
        "unit_price",
        "subtotal",  # Read-only — computed by SaleItem.save()
    )

    # subtotal is auto-calculated in the model's save() method; making it
    # readonly prevents accidental manual edits and signals intent clearly.
    readonly_fields = ("subtotal",)

    # Use a search popup for product selection — avoids a massive <select>
    # if there are hundreds of products in the catalogue.
    raw_id_fields = ("product",)


# ---------------------------------------------------------------------------
# Sale admin
# ---------------------------------------------------------------------------

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Admin interface for the Sale (invoice) model.

    The SaleItemInline embeds all line items so an entire invoice can be
    created and edited from a single page.
    """

    inlines = [SaleItemInline]

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "invoice_number",
        "sold_by",       # Renders via User.__str__
        "total_amount",
        "sale_date",
    )

    list_display_links = ("invoice_number",)

    list_filter = ("sale_date",)   # Date-based sidebar filter

    search_fields = (
        "invoice_number",          # Direct match on invoice number
        "sold_by__username",       # Traverse the FK to find by username
        "sold_by__first_name",
        "sold_by__last_name",
    )

    # Most recent sales first
    ordering = ("-sale_date",)

    # Date drill-down navigation bar
    date_hierarchy = "sale_date"

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    # Once an invoice is created, its number and date should not be changed
    # to preserve the financial audit trail.  total_amount is also readonly
    # because it should be recalculated from line items by application code,
    # not typed in manually.
    readonly_fields = ("invoice_number", "sale_date", "total_amount")

    fieldsets = (
        (
            "Invoice Header",
            {
                "fields": (
                    "invoice_number",
                    "sold_by",
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


# ---------------------------------------------------------------------------
# SaleItem admin (standalone — for viewing / filtering individual line items)
# ---------------------------------------------------------------------------

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    """
    Standalone admin for individual SaleItem records.

    Useful for auditing purposes — e.g. "show me every sale that included
    Product X" — without having to open each invoice manually.

    Note: Creating new SaleItems here bypasses the Sale total_amount update
    and stock deduction guard only if done carelessly; prefer the inline on
    the Sale change form for normal operations.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "sale",        # Invoice this item belongs to
        "product",     # Renders via Product.__str__
        "quantity",
        "unit_price",
        "subtotal",    # Stored value; auto-computed on save
    )

    list_display_links = ("sale", "product")

    list_filter = (
        "sale__sale_date",  # Traverse FK to filter by invoice date
        "product",
    )

    search_fields = (
        "sale__invoice_number",    # Search by invoice number
        "product__product_name",   # Search by product name
        "product__sku",            # Search by SKU
    )

    ordering = ("-sale__sale_date", "id")

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    # subtotal is auto-computed; sale is the parent — both readonly here
    # to reinforce that these should be managed via the Sale inline.
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
