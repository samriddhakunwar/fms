from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrInventoryManagerOrStaffReadOnly

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Finished-products inventory.

    ADMIN and INVENTORY_MANAGER get full CRUD. STAFF is read-only: they
    can see stock levels but cannot add, update or delete items.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrInventoryManagerOrStaffReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["product_name", "sku"]
    ordering_fields = ["product_name", "selling_price", "quantity_in_stock", "created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        low_stock = self.request.query_params.get("low_stock")
        if low_stock == "true":
            from django.db.models import F

            queryset = queryset.filter(quantity_in_stock__lte=F("minimum_stock_level"))
        return queryset

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
