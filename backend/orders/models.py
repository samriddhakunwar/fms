from decimal import Decimal
from typing import Callable

from django.db import models
from django.utils import timezone


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Order Number",
        help_text="Unique identifier for this order.",
    )
    customer_name = models.CharField(
        max_length=255,
        verbose_name="Customer",
        help_text="The customer or company that placed this order.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Total Amount",
        help_text="Grand total of all line items on this order.",
    )
    order_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Order Date",
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Expected Delivery Date",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )

    items: "models.Manager[OrderItem]"
    get_status_display: Callable[[], str]

    class Meta:
        db_table = "customer_order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-order_date"]

    def __str__(self):
        return (
            f"Order #{self.order_number} — {self.customer_name} — "
            f"{self.total_amount} ({self.get_status_display()})"
        )

    @property
    def is_open(self) -> bool:
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)

    def recalculate_total(self, save=True):
        total = sum(
            (item.subtotal for item in self.items.all()), Decimal("0")
        )
        self.total_amount = total
        if save:
            self.save(update_fields=["total_amount"])
        return total


class OrderItem(models.Model):
    """One product line on an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Order",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Product",
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantity Ordered",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Unit Price",
        help_text="Price per unit at the time the order was placed.",
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Subtotal",
        help_text="quantity × unit_price — computed on save.",
    )

    class Meta:
        db_table = "customer_order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["id"]

    def __str__(self):
        return (
            f"{self.quantity} × {self.product.product_name} "
            f"@ {self.unit_price} = {self.subtotal}"
        )

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
