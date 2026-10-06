from django.db import transaction
from django.db.models import F
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.activity import ViewLoggingMixin
from accounts.models import User
from accounts.permissions import IsAdminOrManager, IsAdminOrManagerOrStaffReadOnly
from fms.actor import ActorMixin, role_fields

from .models import Product, StockMovement
from .serializers import (
    ProductSerializer,
    StockAdjustmentSerializer,
    StockMovementSerializer,
)


ROLE_JOINS = (
    "created_by_admin__user",
    "created_by_manager__user",
    "updated_by_admin__user",
    "updated_by_manager__user",
)
MOVEMENT_JOINS = ("product", "sale", "admin__user", "manager__user")


class ProductViewSet(ActorMixin, ViewLoggingMixin, viewsets.ModelViewSet):
    """Finished-products inventory."""

    queryset = Product.objects.select_related(*ROLE_JOINS)
    view_log_target = "product"
    view_log_roles = (User.Role.STAFF,)
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrManagerOrStaffReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["product_name", "sku"]
    ordering_fields = ["product_name", "selling_price", "quantity_in_stock", "created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        low_stock = self.request.query_params.get("low_stock")
        if low_stock == "true":
            queryset = queryset.filter(quantity_in_stock__lte=F("minimum_stock_level"))
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        product = serializer.save(**role_fields(self.request.user, "created_by_"))
        StockMovement.record(
            product,
            product.quantity_in_stock,
            StockMovement.MovementType.STOCK_IN,
            self.request.user,
            "Opening stock",
        )

    @transaction.atomic
    def perform_update(self, serializer):
        # Lock the row so the logged difference matches what is overwritten.
        previous = (
            Product.objects.select_for_update()
            .values_list("quantity_in_stock", flat=True)
            .get(pk=serializer.instance.pk)
        )
        product = serializer.save(**role_fields(self.request.user, "updated_by_"))
        StockMovement.record(
            product,
            product.quantity_in_stock - previous,
            StockMovement.MovementType.ADJUSTMENT,
            self.request.user,
            "Stock quantity edited",
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        products = self.get_queryset()
        total = products.count()
        low_stock = sum(1 for p in products if p.is_low_stock())
        out_of_stock = sum(1 for p in products if p.quantity_in_stock == 0)
        return Response(
            {
                "total_products": total,
                "low_stock_products": low_stock,
                "out_of_stock_products": out_of_stock,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrManager],
        url_path="adjust-stock",
    )
    def adjust_stock(self, request, pk=None):
        """Add or remove units, logging the change as a stock movement."""
        self.get_object()  # 404 for an unknown product
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change = serializer.validated_data["quantity_change"]

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=pk)
            new_quantity = product.quantity_in_stock + change
            if new_quantity < 0:
                return Response(
                    {
                        "quantity_change": (
                            f"Cannot remove {-change} units: only "
                            f"{product.quantity_in_stock} in stock."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.quantity_in_stock = new_quantity
            stamp = role_fields(request.user, "updated_by_")
            for field, profile in stamp.items():
                setattr(product, field, profile)
            product.save(update_fields=["quantity_in_stock", "updated_at", *stamp])
            movement = StockMovement.record(
                product,
                change,
                serializer.validated_data["movement_type"],
                request.user,
                serializer.validated_data.get("reason", ""),
            )

        return Response(
            {
                "product": ProductSerializer(product).data,
                "movement": StockMovementSerializer(movement).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrManager])
    def movements(self, request, pk=None):
        product = self.get_object()
        movements = product.stock_movements.select_related(*MOVEMENT_JOINS)
        return Response(StockMovementSerializer(movements, many=True).data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """Every logged change to stock levels, newest first. Read-only."""

    queryset = StockMovement.objects.select_related(*MOVEMENT_JOINS)
    serializer_class = StockMovementSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        product = params.get("product")
        if product:
            if not product.isdigit():
                raise ValidationError({"product": "product must be a product id."})
            queryset = queryset.filter(product_id=product)
        movement_type = params.get("movement_type")
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type.upper())
        return queryset
