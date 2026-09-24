from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR

from .models import Product


# Custom list filter
class LowStockFilter(admin.SimpleListFilter):
    title = "Stock Level"          # Label shown in the sidebar
    parameter_name = "low_stock"   # URL query string key

    def lookups(self, request, model_admin):
        return (
            ("yes", "⚠  Low Stock"),
            ("no",  "✅ In Stock"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            # Return products where stock ≤ minimum_stock_level
            from django.db.models import F
            return queryset.filter(quantity_in_stock__lte=F("minimum_stock_level"))
        if self.value() == "no":
            # Return products where stock > minimum_stock_level
            from django.db.models import F
            return queryset.filter(quantity_in_stock__gt=F("minimum_stock_level"))
        return queryset


# Product admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # List view
    list_display = (
        "product_name",
        "sku",
        "selling_price",
        "quantity_in_stock",
        "minimum_stock_level",
        "stock_status",
        "is_active",
        "created_at",
    )

    list_display_links = ("product_name", "sku")

    list_filter = (
        "is_active",        # Retired vs. sellable products
        LowStockFilter,     # Custom sidebar filter defined above
        "created_at",       # Django's built-in date hierarchy filter
    )

    search_fields = ("product_name", "sku", "description")

    actions = ("deactivate_products", "reactivate_products")

    ordering = ("product_name",)

    date_hierarchy = "created_at"

    # Detail (add / change) view
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
                "classes": ("collapse",),
            },
        ),
    )

    # Deletion policy
    def has_delete_permission(self, request, obj=None):
        return False

    # Actions
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

    # Querysets
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "is_active__exact" not in request.GET:
            queryset = queryset.filter(is_active=True)
        return queryset

    # Custom admin methods
    @admin.display(
        description="Stock Status",   # Column header text
        ordering="quantity_in_stock",
    )
    def stock_status(self, obj: Product) -> str:
        if obj.is_low_stock():
            return "⚠ Low Stock"
        return "✅ In Stock"
