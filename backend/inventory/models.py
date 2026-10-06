from typing import Callable

from django.db import models

from fms.actor import admin_of, manager_of, role_name
from fms.constraints import at_most_one_role


class Product(models.Model):

    product_name = models.CharField(
        max_length=255,
        verbose_name="Product Name",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Detailed description of the product.",
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="SKU",
        help_text="Stock Keeping Unit — must be unique across all products.",
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Selling Price",
        help_text="Price at which this product is sold to customers.",
    )
    quantity_in_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantity in Stock",
        help_text="Current number of units available in the warehouse.",
    )
    minimum_stock_level = models.PositiveIntegerField(
        default=0,
        verbose_name="Minimum Stock Level",
        help_text=(
            "When quantity_in_stock falls to or below this value, "
            "the product is considered low stock."
        ),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text=(
            "Uncheck to retire this product instead of deleting it. Inactive "
            "products stay in the catalogue so past invoices remain intact, "
            "but cannot be added to new sales."
        ),
    )
    created_by_admin = models.ForeignKey(
        "accounts.AdminProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_created",
        verbose_name="Created By (Admin)",
        help_text="The Admin who added this product, if an Admin did.",
    )
    created_by_manager = models.ForeignKey(
        "accounts.ManagerProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_created",
        verbose_name="Created By (Manager)",
        help_text="The Manager who added this product, if a Manager did.",
    )
    updated_by_admin = models.ForeignKey(
        "accounts.AdminProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_updated",
        verbose_name="Last Updated By (Admin)",
        help_text="The Admin who last edited this product, if an Admin did.",
    )
    updated_by_manager = models.ForeignKey(
        "accounts.ManagerProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_updated",
        verbose_name="Last Updated By (Manager)",
        help_text="The Manager who last edited this product, if a Manager did.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    created_by_admin_id: int | None
    created_by_manager_id: int | None
    updated_by_admin_id: int | None
    updated_by_manager_id: int | None

    class Meta:
        db_table = "product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["product_name"]
        constraints = [
            at_most_one_role(
                "created_by_admin", "created_by_manager", "product_created_by_one_role"
            ),
            at_most_one_role(
                "updated_by_admin", "updated_by_manager", "product_updated_by_one_role"
            ),
        ]

    def __str__(self):
        return f"{self.product_name} (SKU: {self.sku})"

    @property
    def created_by_name(self):
        return role_name(self.created_by_admin, self.created_by_manager)

    @property
    def updated_by_name(self):
        return role_name(self.updated_by_admin, self.updated_by_manager)

    def is_low_stock(self) -> bool:
        return self.quantity_in_stock <= self.minimum_stock_level


class StockMovement(models.Model):
    """
    One change to a product's quantity_in_stock: who made it, why, and what the
    stock level was afterwards. Rows are written alongside the change itself
    and are never edited.
    """

    class MovementType(models.TextChoices):
        STOCK_IN = "STOCK_IN", "Stock In"
        STOCK_OUT = "STOCK_OUT", "Stock Out"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        SALE = "SALE", "Sale"
        SALE_RETURN = "SALE_RETURN", "Sale Return"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name="Product",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name="Movement Type",
    )
    quantity_change = models.IntegerField(
        verbose_name="Quantity Change",
        help_text="Units added (positive) or removed (negative).",
    )
    quantity_after = models.PositiveIntegerField(
        verbose_name="Quantity After",
        help_text="quantity_in_stock once this change was applied.",
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Reason",
    )
    sale = models.ForeignKey(
        "sales.Sale",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
        verbose_name="Sale",
        help_text="The invoice behind a SALE movement, while it still exists.",
    )
    admin = models.ForeignKey(
        "accounts.AdminProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
        verbose_name="Admin",
        help_text="The Admin who made this change, if an Admin did.",
    )
    manager = models.ForeignKey(
        "accounts.ManagerProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
        verbose_name="Manager",
        help_text="The Manager who made this change, if a Manager did.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    admin_id: int | None
    manager_id: int | None
    get_movement_type_display: Callable[[], str]

    class Meta:
        db_table = "stock_movement"
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ["-created_at", "-id"]
        constraints = [
            at_most_one_role("admin", "manager", "stock_movement_one_role"),
        ]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} {self.quantity_change:+d} × "
            f"{self.product.product_name} → {self.quantity_after}"
        )

    @property
    def performed_by_name(self):
        return role_name(self.admin, self.manager)

    @classmethod
    def record(cls, product, change, movement_type, user=None, reason="", sale=None):
        """
        Log a change that has already been applied to product.quantity_in_stock,
        crediting the user's Admin or Manager record. Zero changes are not
        logged.
        """
        if not change:
            return None
        return cls.objects.create(
            product=product,
            movement_type=movement_type,
            quantity_change=change,
            quantity_after=product.quantity_in_stock,
            reason=(reason or "")[:255],
            sale=sale,
            admin=admin_of(user),
            manager=manager_of(user),
        )
