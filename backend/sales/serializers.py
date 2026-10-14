from django.db import transaction
from rest_framework import serializers

from fms.numbers import unique_number
from inventory.models import Product

from .models import Sale, SaleItem


class SaleItemInputSerializer(serializers.Serializer):
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
    items_input = SaleItemInputSerializer(many=True, write_only=True, required=False)
    order_number = serializers.CharField(
        source="order.order_number", read_only=True, default=None
    )
    created_by_name = serializers.StringRelatedField(source="created_by_admin")
    updated_by_name = serializers.StringRelatedField(source="updated_by_admin")

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
            "created_by_admin",
            "created_by_name",
            "updated_by_admin",
            "updated_by_name",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "total_amount",
            "sale_date",
            "order",
            "order_number",
            "items",
            "created_by_admin",
            "updated_by_admin",
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

    def _write_items(self, sale, items_data):
        try:
            sale.add_items(
                (item["product"], item["quantity"], item["product"].selling_price)
                for item in items_data
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def create(self, validated_data):
        items_data = validated_data.pop("items_input")

        with transaction.atomic():
            sale = Sale.objects.create(
                invoice_number=unique_number(Sale, "invoice_number", "INV"),
                sold_to=validated_data["sold_to"],
                created_by_admin=validated_data.get("created_by_admin"),
            )
            self._write_items(sale, items_data)

        return sale

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_input", None)

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()

            if items_data is not None:
                instance.items.all().delete()  # restores stock
                self._write_items(instance, items_data)

        instance.refresh_from_db()
        return instance
