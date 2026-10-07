from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR
from django.db import transaction
from django.db.models import F

from accounts.admin import ReadOnlyAdmin
from fms.actor import stamp

from .models import Product, StockMovement


class LowStockFilter(admin.SimpleListFilter):
    title = "Stock Level"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return (
            ("yes", "⚠  Low Stock"),
            ("no",  "✅ In Stock"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(quantity_in_stock__lte=F("minimum_stock_level"))
        if self.value() == "no":
            return queryset.filter(quantity_in_stock__gt=F("minimum_stock_level"))
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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

    list_filter = ("is_active", LowStockFilter, "created_at")

    search_fields = ("product_name", "sku", "description")

    actions = ("deactivate_products", "reactivate_products")

    ordering = ("product_name",)

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
        stamp(obj, request.user, "updated_by_" if change else "created_by_")
        previous = 0
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
            StockMovement.MovementType.ADJUSTMENT if change else StockMovement.MovementType.STOCK_IN,
            request.user,
            "Stock quantity edited in Django admin" if change else "Opening stock",
        )

    def has_delete_permission(self, request, obj=None):
        return False

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "is_active__exact" not in request.GET:
            queryset = queryset.filter(is_active=True)
        return queryset

    @admin.display(description="Stock Status", ordering="quantity_in_stock")
    def stock_status(self, obj: Product) -> str:
        if obj.is_low_stock():
            return "⚠ Low Stock"
        return "✅ In Stock"


@admin.register(StockMovement)
class StockMovementAdmin(ReadOnlyAdmin):
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
