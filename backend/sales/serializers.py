import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from inventory.models import Product

from .models import Sale, SaleItem


def generate_invoice_number():
    for _ in range(5):
        candidate = f"INV-{uuid.uuid4().hex[:10].upper()}"
        if not Sale.objects.filter(invoice_number=candidate).exists():
            return candidate
    raise RuntimeError("Could not generate a unique invoice number.")


class SaleItemInputSerializer(serializers.Serializer):
    # Retired products stay on their old invoices but cannot be sold again.
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "subtotal"]
        read_only_fields = ["id", "unit_price", "subtotal"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    items_input = SaleItemInputSerializer(many=True, write_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "invoice_number",
            "sold_to",
            "total_amount",
            "sale_date",
            "items",
            "items_input",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "total_amount",
            "sale_date",
            "items",
        ]

    def validate_items_input(self, value):
        if not value:
            raise serializers.ValidationError("A sale must include at least one item.")
        return value

    def validate_sold_to(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Customer name is required.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items_input")

        with transaction.atomic():
            sale = Sale.objects.create(
                invoice_number=generate_invoice_number(),
                sold_to=validated_data["sold_to"],
            )

            total = Decimal("0")
            for item in items_data:
                product = item["product"]
                sale_item = SaleItem(
                    sale=sale,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.selling_price,
                )
                try:
                    sale_item.save()
                except ValueError as exc:
                    raise serializers.ValidationError(str(exc))
                total += sale_item.subtotal

            sale.total_amount = total
            sale.save(update_fields=["total_amount"])

        return sale
