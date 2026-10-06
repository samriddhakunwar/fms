from rest_framework import serializers

from .models import Product, StockMovement


class ProductSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(read_only=True)
    updated_by_name = serializers.CharField(read_only=True)

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
            "created_by_admin",
            "created_by_manager",
            "created_by_name",
            "updated_by_admin",
            "updated_by_manager",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_admin",
            "created_by_manager",
            "updated_by_admin",
            "updated_by_manager",
            "created_at",
            "updated_at",
        ]

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


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    invoice_number = serializers.CharField(
        source="sale.invoice_number", read_only=True, default=None
    )
    performed_by_name = serializers.CharField(read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "movement_type",
            "quantity_change",
            "quantity_after",
            "reason",
            "sale",
            "invoice_number",
            "admin",
            "manager",
            "performed_by_name",
            "created_at",
        ]
        read_only_fields = fields


# Sales and their returns are logged by the sales app, never entered by hand.
MANUAL_MOVEMENT_TYPES = [
    StockMovement.MovementType.STOCK_IN,
    StockMovement.MovementType.STOCK_OUT,
    StockMovement.MovementType.ADJUSTMENT,
]


class StockAdjustmentSerializer(serializers.Serializer):
    quantity_change = serializers.IntegerField()
    movement_type = serializers.ChoiceField(
        choices=MANUAL_MOVEMENT_TYPES,
        default=StockMovement.MovementType.ADJUSTMENT,
    )
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity change cannot be zero.")
        return value

    def validate(self, attrs):
        change = attrs["quantity_change"]
        movement_type = attrs["movement_type"]
        if movement_type == StockMovement.MovementType.STOCK_IN and change < 0:
            raise serializers.ValidationError(
                {"quantity_change": "Stock in must add units (use a positive number)."}
            )
        if movement_type == StockMovement.MovementType.STOCK_OUT and change > 0:
            raise serializers.ValidationError(
                {"quantity_change": "Stock out must remove units (use a negative number)."}
            )
        return attrs
