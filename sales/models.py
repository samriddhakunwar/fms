from django.conf import settings
from django.db import models
from django.utils import timezone


class Sale(models.Model):


    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Invoice Number",
        help_text="Unique identifier for this sale/invoice.",
    )
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name="Sold By",
        help_text="The system user who recorded this sale.",
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Total Amount",
        help_text="Grand total of all line items in this invoice.",
    )
    sale_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Sale Date",
    )

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Invoice #{self.invoice_number} — {self.total_amount} on {self.sale_date.strftime('%Y-%m-%d')}"


class SaleItem(models.Model):
    """
    Represents a single line item within a Sale (one product, its quantity,
    and computed subtotal).

    Business logic in save():
      1. Prevents the sale if stock is insufficient (raises ValueError).
      2. Reduces product.quantity_in_stock by the sold quantity.
      3. Saves the updated product record.

    The product FK uses PROTECT so you cannot delete a product
    that has ever been sold — preserving the sales audit trail.
    """

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Sale",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
        verbose_name="Product",
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantity Sold",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Unit Price",
        help_text=(
            "Price per unit at the time of sale. Stored explicitly so "
            "historical records remain accurate if the product price changes later."
        ),
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Subtotal",
        help_text="quantity × unit_price — computed and stored on save.",
    )

    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.quantity} × {self.product.product_name} "
            f"@ {self.unit_price} = {self.subtotal}"
        )

    # ------------------------------------------------------------------ #
    # Business logic — stock management                                   #
    # ------------------------------------------------------------------ #

    def save(self, *args, **kwargs):
        """
        Custom save that enforces stock constraints and reduces inventory.

        Only deducts stock on creation (not on update) to avoid double-
        deduction if the record is ever re-saved.

        Raises:
            ValueError: If there is not enough stock to fulfil the sale.
        """
        is_new = self.pk is None  # True only when inserting a new record

        if is_new:
            product = self.product

            # 1. Guard: ensure sufficient stock exists before proceeding.
            if self.quantity > product.quantity_in_stock:
                raise ValueError(
                    f"Insufficient stock for '{product.product_name}'. "
                    f"Requested: {self.quantity}, "
                    f"Available: {product.quantity_in_stock}."
                )

            # 2. Compute subtotal (quantity × unit_price).
            self.subtotal = self.quantity * self.unit_price

            # 3. Deduct sold quantity from inventory.
            product.quantity_in_stock -= self.quantity

            # 4. Persist the updated product stock level.
            #    The is_low_stock() check can be read by any downstream
            #    view or signal — no extra flag needed on the model.
            product.save(update_fields=["quantity_in_stock", "updated_at"])

        super().save(*args, **kwargs)
