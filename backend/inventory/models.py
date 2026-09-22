from django.db import models


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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["product_name"]

    def __str__(self):
        return f"{self.product_name} (SKU: {self.sku})"

    # ------------------------------------------------------------------ #
    # Business logic                                                       #
    # ------------------------------------------------------------------ #

    def is_low_stock(self) -> bool:
        """
        Returns True if the current stock is at or below the minimum stock level.

        This is checked automatically after every sale (see SaleItem.save()).
        """
        return self.quantity_in_stock <= self.minimum_stock_level
