import uuid

from django.db import transaction
from rest_framework import serializers

from inventory.models import Product

from .models import Order, OrderItem


def generate_order_number():
    for _ in range(5):
        candidate = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        if not Order.objects.filter(order_number=candidate).exists():
            return candidate
    raise RuntimeError("Could not generate a unique order number.")


class OrderItemInputSerializer(serializers.Serializer):
    # Retired products stay on their old orders but cannot be ordered again.
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "quantity",
            "unit_price",
            "subtotal",
        ]
        read_only_fields = ["id", "unit_price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_input = OrderItemInputSerializer(many=True, write_only=True, required=False)
    invoice_number = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_name",
            "status",
            "total_amount",
            "order_date",
            "expected_delivery_date",
            "notes",
            "items",
            "items_input",
            "invoice_number",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "total_amount",
            "order_date",
            "items",
        ]

    def get_invoice_number(self, obj):
        """The invoice this order became, once it has been fulfilled."""
        sale = getattr(obj, "sale", None)
        return sale.invoice_number if sale else None

    def validate_customer_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Customer name is required.")
        return value

    def validate_items_input(self, value):
        if not value:
            raise serializers.ValidationError("An order must include at least one item.")
        return value

    def validate(self, attrs):
        # Only enforced on create; an update may legitimately leave the lines
        # alone and change only the header fields.
        if self.instance is None and not attrs.get("items_input"):
            raise serializers.ValidationError(
                {"items_input": "An order must include at least one item."}
            )
        return attrs

    def _write_items(self, order, items_data):
        """Replaces the order's lines. No stock moves — orders never touch it."""
        order.items.all().delete()
        for item in items_data:
            product = item["product"]
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                unit_price=product.selling_price,
            )
        order.recalculate_total()

    def create(self, validated_data):
        items_data = validated_data.pop("items_input")

        with transaction.atomic():
            order = Order.objects.create(
                order_number=generate_order_number(),
                **validated_data,
            )
            self._write_items(order, items_data)

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_input", None)

        # A fulfilled order has an invoice hanging off it and a stock movement
        # behind it; editing it after the fact would silently diverge from the
        # sale. Cancelled orders are closed for the same reason.
        if not instance.is_open:
            raise serializers.ValidationError(
                f"A {instance.get_status_display().lower()} order can no longer "
                "be edited."
            )

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()

            if items_data is not None:
                self._write_items(instance, items_data)

        instance.refresh_from_db()
        return instance
