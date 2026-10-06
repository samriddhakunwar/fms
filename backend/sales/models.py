from decimal import Decimal

from django.db import models, transaction
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone


class Sale(models.Model):


    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Invoice Number",
        help_text="Unique identifier for this sale/invoice.",
    )
    sold_to = models.CharField(
        max_length=255,
        verbose_name="Sold To",
        help_text="The customer or company this invoice was issued to.",
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Total Amount",
        help_text="Grand total of all line items in this invoice.",
    )
    sale_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Sale Date",
    )
    order = models.OneToOneField(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sale",
        verbose_name="Order",
        help_text=(
            "The customer order this invoice was raised from, if any. Walk-in "
            "sales recorded directly have no order behind them, so this is "
            "optional; if the order is later removed the invoice survives "
            "without it."
        ),
    )
    # Only Admins record or change sales (Managers are view-only), so there
    # is no Manager column here.
    created_by_admin = models.ForeignKey(
        "accounts.AdminProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales_created",
        verbose_name="Recorded By (Admin)",
        help_text=(
            "The Admin who recorded this sale. Empty for sales recorded before "
            "this was tracked, or if that Admin was later deleted."
        ),
    )
    updated_by_admin = models.ForeignKey(
        "accounts.AdminProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales_updated",
        verbose_name="Last Updated By (Admin)",
        help_text="The Admin who last edited this sale.",
    )

    items: "models.Manager[SaleItem]"
    created_by_admin_id: int | None
    updated_by_admin_id: int | None

    class Meta:
        db_table = "sale"
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ["-sale_date"]

    def __str__(self):
        return (
            f"Invoice #{self.invoice_number} — {self.sold_to} — "
            f"{self.total_amount} on {self.sale_date.strftime('%Y-%m-%d')}"
        )


class SaleItem(models.Model):
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

    product_id: int

    class Meta:
        db_table = "sale_item"
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.quantity} × {self.product.product_name} "
            f"@ {self.unit_price} = {self.subtotal}"
        )

    def _stock_actor(self):
        """The request user, else the login of the Admin who recorded the sale."""
        from fms.actor import get_current_actor

        actor = get_current_actor()
        if actor is None and self.sale.created_by_admin_id:
            actor = self.sale.created_by_admin.user
        return actor

    def _log_stock(self, product, change):
        from inventory.models import StockMovement

        movement_type = (
            StockMovement.MovementType.SALE
            if change < 0
            else StockMovement.MovementType.SALE_RETURN
        )
        StockMovement.record(
            product,
            change,
            movement_type,
            self._stock_actor(),
            f"Invoice {self.sale.invoice_number}",
            self.sale,
        )

    def save(self, *args, **kwargs):
        from inventory.models import Product

        is_new = self.pk is None

        with transaction.atomic():
            if is_new:
                product = Product.objects.select_for_update().get(pk=self.product_id)

                if self.quantity > product.quantity_in_stock:
                    raise ValueError(
                        f"Insufficient stock for '{product.product_name}'. "
                        f"Requested: {self.quantity}, "
                        f"Available: {product.quantity_in_stock}."
                    )

                self.subtotal = self.quantity * self.unit_price
                product.quantity_in_stock -= self.quantity
                product.save(update_fields=["quantity_in_stock", "updated_at"])
                self._log_stock(product, -self.quantity)
            else:
                previous = SaleItem.objects.get(pk=self.pk)

                if previous.product_id == self.product_id:
                    product = Product.objects.select_for_update().get(pk=self.product_id)
                    delta = self.quantity - previous.quantity  # + means selling more

                    if delta > 0 and delta > product.quantity_in_stock:
                        raise ValueError(
                            f"Insufficient stock for '{product.product_name}'. "
                            f"Additional units requested: {delta}, "
                            f"Available: {product.quantity_in_stock}."
                        )

                    product.quantity_in_stock -= delta
                    product.save(update_fields=["quantity_in_stock", "updated_at"])
                    self._log_stock(product, -delta)
                else:
                    old_product = Product.objects.select_for_update().get(
                        pk=previous.product_id
                    )
                    old_product.quantity_in_stock += previous.quantity
                    old_product.save(update_fields=["quantity_in_stock", "updated_at"])
                    self._log_stock(old_product, previous.quantity)

                    new_product = Product.objects.select_for_update().get(
                        pk=self.product_id
                    )
                    if self.quantity > new_product.quantity_in_stock:
                        raise ValueError(
                            f"Insufficient stock for '{new_product.product_name}'. "
                            f"Requested: {self.quantity}, "
                            f"Available: {new_product.quantity_in_stock}."
                        )
                    new_product.quantity_in_stock -= self.quantity
                    new_product.save(update_fields=["quantity_in_stock", "updated_at"])
                    self._log_stock(new_product, -self.quantity)

                self.subtotal = self.quantity * self.unit_price

            super().save(*args, **kwargs)


@receiver(pre_delete, sender=SaleItem)
def restore_stock_on_saleitem_delete(sender, instance, **kwargs):
    from inventory.models import Product, StockMovement

    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=instance.product_id)
        product.quantity_in_stock += instance.quantity
        product.save(update_fields=["quantity_in_stock", "updated_at"])
        # The sale may be deleted in this same cascade, so the movement is not
        # linked to it; the invoice number in the reason keeps it traceable.
        StockMovement.record(
            product,
            instance.quantity,
            StockMovement.MovementType.SALE_RETURN,
            instance._stock_actor(),
            f"Invoice {instance.sale.invoice_number}: line removed",
        )


@receiver(post_delete, sender=Sale)
def reopen_order_on_sale_delete(sender, instance, **kwargs):
    if instance.order_id is None:
        return

    from orders.models import Order

    Order.objects.filter(pk=instance.order_id, status=Order.Status.FULFILLED).update(
        status=Order.Status.CONFIRMED
    )
