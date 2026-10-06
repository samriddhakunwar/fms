from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR
from django.db import transaction

from fms.actor import role_fields

from .models import Product, StockMovement


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
    readonly_fields = (
        "created_by_admin",
        "created_by_manager",
        "updated_by_admin",
        "updated_by_manager",
        "created_at",
        "updated_at",
    )

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
                "fields": (
                    "created_by_admin",
                    "created_by_manager",
                    "updated_by_admin",
                    "updated_by_manager",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        stamp = "updated_by_" if change else "created_by_"
        for field, profile in role_fields(request.user, stamp).items():
            setattr(obj, field, profile)
        if change:
            previous = (
                Product.objects.select_for_update()
                .values_list("quantity_in_stock", flat=True)
                .get(pk=obj.pk)
            )
            super().save_model(request, obj, form, change)
            StockMovement.record(
                obj,
                obj.quantity_in_stock - previous,
                StockMovement.MovementType.ADJUSTMENT,
                request.user,
                "Stock quantity edited in Django admin",
            )
        else:
            super().save_model(request, obj, form, change)
            StockMovement.record(
                obj,
                obj.quantity_in_stock,
                StockMovement.MovementType.STOCK_IN,
                request.user,
                "Opening stock",
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


# Stock movement admin (read-only ledger)
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Written automatically whenever stock changes; never edited by hand."""

    list_display = (
        "created_at",
        "product",
        "movement_type",
        "quantity_change",
        "quantity_after",
        "admin",
        "manager",
        "sale",
        "reason",
    )
    list_select_related = ("product", "admin__user", "manager__user", "sale")
    list_filter = ("movement_type", "created_at")
    search_fields = ("product__product_name", "product__sku", "reason", "sale__invoice_number")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
