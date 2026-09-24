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

    items: "models.Manager[SaleItem]"

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
                else:
                    old_product = Product.objects.select_for_update().get(
                        pk=previous.product_id
                    )
                    old_product.quantity_in_stock += previous.quantity
                    old_product.save(update_fields=["quantity_in_stock", "updated_at"])

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

                self.subtotal = self.quantity * self.unit_price

            super().save(*args, **kwargs)


@receiver(pre_delete, sender=SaleItem)
def restore_stock_on_saleitem_delete(sender, instance, **kwargs):
    from inventory.models import Product

    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=instance.product_id)
        product.quantity_in_stock += instance.quantity
        product.save(update_fields=["quantity_in_stock", "updated_at"])


@receiver(post_delete, sender=Sale)
def reopen_order_on_sale_delete(sender, instance, **kwargs):
    if instance.order_id is None:
        return

    from orders.models import Order

    Order.objects.filter(pk=instance.order_id, status=Order.Status.FULFILLED).update(
        status=Order.Status.CONFIRMED
    )
