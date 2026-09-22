"""
inventory/admin.py
==================
Admin configuration for the Product model.

Highlights:
  • stock_status() — a custom column that delegates to Product.is_low_stock()
    and renders a coloured emoji indicator so staff can spot shortages at a
    glance without opening each record.
  • LowStockFilter — a simple list filter that lets admins quickly narrow the
    list to only products that are below (or above) their minimum stock level.
  • Deletion is disabled. SaleItem.product is PROTECTed to preserve the sales
    audit trail, so a product that has ever been sold can never be deleted.
    Retire it with the "Deactivate" action instead — it stays in the
    catalogue and on old invoices, but is no longer offered for new sales.
"""

from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR

from .models import Product


# ---------------------------------------------------------------------------
# Custom list filter
# ---------------------------------------------------------------------------

class LowStockFilter(admin.SimpleListFilter):
    """
    Sidebar filter: allows filtering by whether a product is low on stock.

    Django requires `title` (human-readable), `parameter_name` (URL query
    key), `lookups()` (choices), and `queryset()` (the actual filter logic).
    """

    title = "Stock Level"          # Label shown in the sidebar
    parameter_name = "low_stock"   # URL query string key

    def lookups(self, request, model_admin):
        """Return the choices that appear in the sidebar filter panel."""
        return (
            ("yes", "⚠  Low Stock"),
            ("no",  "✅ In Stock"),
        )

    def queryset(self, request, queryset):
        """Filter the queryset based on the selected choice."""
        if self.value() == "yes":
            # Return products where stock ≤ minimum_stock_level
            from django.db.models import F
            return queryset.filter(quantity_in_stock__lte=F("minimum_stock_level"))
        if self.value() == "no":
            # Return products where stock > minimum_stock_level
            from django.db.models import F
            return queryset.filter(quantity_in_stock__gt=F("minimum_stock_level"))
        return queryset


# ---------------------------------------------------------------------------
# Product admin
# ---------------------------------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for the inventory Product model.

    Custom column `stock_status` wraps the model's `is_low_stock()` method
    with a human-friendly emoji so warehouse staff immediately see which items
    need reordering.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "product_name",
        "sku",
        "selling_price",
        "quantity_in_stock",
        "minimum_stock_level",
        "stock_status",     # ← custom computed column (see method below)
        "is_active",
        "created_at",
    )

    # These fields produce clickable links / can be sorted
    list_display_links = ("product_name", "sku")

    list_filter = (
        "is_active",        # Retired vs. sellable products
        LowStockFilter,     # Custom sidebar filter defined above
        "created_at",       # Django's built-in date hierarchy filter
    )

    search_fields = ("product_name", "sku", "description")

    actions = ("deactivate_products", "reactivate_products")

    # Default sort: ascending by product name (overrides model Meta ordering
    # in the admin if you'd prefer a different default here)
    ordering = ("product_name",)

    # Date drill-down bar at the top of the changelist
    date_hierarchy = "created_at"

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    # Auto-managed timestamps should never be editable
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Product Information",
            {
                "fields": (
                    "product_name",
                    "sku",
                    "description",
                    "is_active",
                ),
            },
        ),
        (
            "Pricing",
            {
                "fields": ("selling_price",),
            },
        ),
        (
            "Stock Management",
            {
                "fields": (
                    "quantity_in_stock",
                    "minimum_stock_level",
                ),
                "description": (
                    "When quantity_in_stock falls to or below minimum_stock_level "
                    "the product is flagged as low stock."
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),  # Collapsed by default — less visual clutter
            },
        ),
    )

    # ------------------------------------------------------------------
    # Deletion policy
    # ------------------------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        """
        Products are never deleted — retire them with the Deactivate action.

        Returning False also removes the bulk "Delete selected" action, so
        nobody can walk into the ProtectedError that SaleItem.product raises.
        """
        return False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @admin.action(description="Deactivate selected products (soft delete)")
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} product(s) deactivated. They remain on past invoices "
            f"but can no longer be added to new sales.",
        )

    @admin.action(description="Reactivate selected products")
    def reactivate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) reactivated.")

    # ------------------------------------------------------------------
    # Querysets
    # ------------------------------------------------------------------

    def get_queryset(self, request):
        """
        The full catalogue (active and retired) is shown on the changelist,
        but the raw-id chooser popup used when adding a sale line item
        defaults to active products only. An explicit ?is_active__exact=
        in the popup URL still wins, so retired items remain reachable.
        """
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "is_active__exact" not in request.GET:
            queryset = queryset.filter(is_active=True)
        return queryset

    # ------------------------------------------------------------------
    # Custom admin methods
    # ------------------------------------------------------------------

    @admin.display(
        description="Stock Status",   # Column header text
        ordering="quantity_in_stock", # Allow column to be sorted by this field
    )
    def stock_status(self, obj: Product) -> str:
        """
        Display a visual indicator for the product's stock level.

        Delegates to Product.is_low_stock() so the business logic
        lives in exactly one place (the model method).

        Returns:
            "⚠ Low Stock"  — if quantity_in_stock ≤ minimum_stock_level
            "✅ In Stock"  — otherwise
        """
        if obj.is_low_stock():
            return "⚠ Low Stock"
        return "✅ In Stock"
