from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "description",
            "sku",
            "selling_price",
            "quantity_in_stock",
            "minimum_stock_level",
            "is_active",
            "is_low_stock",
            "stock_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_stock_status(self, obj):
        if obj.quantity_in_stock == 0:
            return "OUT_OF_STOCK"
        if obj.is_low_stock():
            return "LOW_STOCK"
        return "IN_STOCK"

    def validate_selling_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")
        return value
