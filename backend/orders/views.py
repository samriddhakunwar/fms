from django.db import transaction
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsAdminOrInventoryManagerNoUpdate
from sales.models import Sale, SaleItem
from sales.serializers import SaleSerializer, generate_invoice_number

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    Customer orders.

    ADMIN has full CRUD. INVENTORY_MANAGER may add, view and delete orders
    but never update one — the role matrix gives managers no amend rights, so
    PUT/PATCH is refused at the API, not merely hidden in the UI. EMPLOYEE has
    no access at all.

    Fulfilling an order (admin only) is what turns it into a sale; see
    ``fulfil`` below.
    """

    queryset = Order.objects.prefetch_related("items__product").select_related("sale")
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrInventoryManagerNoUpdate]
    filter_backends = [filters.SearchFilter]
    search_fields = ["order_number", "customer_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        status_param = params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        if params.get("start_date"):
            queryset = queryset.filter(order_date__date__gte=params["start_date"])
        if params.get("end_date"):
            queryset = queryset.filter(order_date__date__lte=params["end_date"])

        return queryset

    def perform_destroy(self, instance):
        # A fulfilled order is the paper trail behind an invoice; deleting it
        # would leave the sale unexplained. Delete the invoice first.
        if instance.status == Order.Status.FULFILLED:
            raise ValidationError(
                "A fulfilled order cannot be deleted. Delete its invoice first "
                "if the sale was recorded in error."
            )
        instance.delete()

    @action(detail=False, methods=["get"])
    def summary(self, request):
        orders = Order.objects.all()
        return Response(
            {
                "total_orders": orders.count(),
                "pending_orders": orders.filter(status=Order.Status.PENDING).count(),
                "fulfilled_orders": orders.filter(
                    status=Order.Status.FULFILLED
                ).count(),
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def fulfil(self, request, pk=None):
        """
        Turns an open order into a sale: raises the invoice, deducts the stock,
        and marks the order fulfilled.

        Admin-only, because it *creates a sale* — managers may never do that,
        and routing it through this action keeps that boundary in one place.
        The whole thing is one transaction, so a line that outruns stock leaves
        the order and the inventory untouched.
        """
        order = self.get_object()

        if order.status == Order.Status.FULFILLED:
            return Response(
                {"detail": "This order has already been fulfilled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order.status == Order.Status.CANCELLED:
            return Response(
                {"detail": "A cancelled order cannot be fulfilled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = list(order.items.select_related("product"))
        if not items:
            return Response(
                {"detail": "This order has no line items to invoice."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                sale = Sale.objects.create(
                    invoice_number=generate_invoice_number(),
                    sold_to=order.customer_name,
                    order=order,
                )

                total = 0
                for item in items:
                    sale_item = SaleItem(
                        sale=sale,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                    )
                    sale_item.save()  # deducts stock, raises on a shortfall
                    total += sale_item.subtotal

                sale.total_amount = total
                sale.save(update_fields=["total_amount"])

                order.status = Order.Status.FULFILLED
                order.save(update_fields=["status"])
        except ValueError as exc:
            # Raised by SaleItem.save() when stock is insufficient.
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
