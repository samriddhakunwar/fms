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
    # Optional on update: an invoice may be corrected header-only (a
    # misspelled customer) without touching its lines or the stock behind them.
    items_input = SaleItemInputSerializer(many=True, write_only=True, required=False)
    order_number = serializers.CharField(
        source="order.order_number", read_only=True, default=None
    )

    class Meta:
        model = Sale
        fields = [
            "id",
            "invoice_number",
            "sold_to",
            "total_amount",
            "sale_date",
            "order",
            "order_number",
            "items",
            "items_input",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "total_amount",
            "sale_date",
            "order",
            "order_number",
            "items",
        ]

    def validate_items_input(self, value):
        if not value:
            raise serializers.ValidationError("A sale must include at least one item.")
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get("items_input"):
            raise serializers.ValidationError(
                {"items_input": "A sale must include at least one item."}
            )
        return attrs

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

    def update(self, instance, validated_data):
        """
        Corrects an existing invoice (Admin only — see SaleViewSet).

        When the line items are re-sent they are rewritten wholesale: the old
        rows are deleted, which returns their quantities to stock via the
        SaleItem pre_delete signal, and the new rows are saved, which deducts
        again with the usual stock check. Doing it as a replace rather than a
        per-row diff keeps one code path, and the atomic block means a
        correction that outruns stock leaves both the invoice and the
        inventory exactly as they were.

        The invoice number and date are never rewritten — an invoice keeps its
        identity so the audit trail holds.
        """
        items_data = validated_data.pop("items_input", None)

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()

            if items_data is not None:
                instance.items.all().delete()  # restores stock

                total = Decimal("0")
                for item in items_data:
                    product = item["product"]
                    sale_item = SaleItem(
                        sale=instance,
                        product=product,
                        quantity=item["quantity"],
                        unit_price=product.selling_price,
                    )
                    try:
                        sale_item.save()
                    except ValueError as exc:
                        raise serializers.ValidationError(str(exc))
                    total += sale_item.subtotal

                instance.total_amount = total
                instance.save(update_fields=["total_amount"])

        instance.refresh_from_db()
        return instance
