from django.db import transaction
from django.db.models import Count, Q
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsAdminOrManagerNoUpdate
from fms.actor import ActorMixin, admin_of, role_fields
from fms.dates import day_range_filter, parse_day_param
from sales.models import Sale, SaleItem
from sales.serializers import SaleSerializer, generate_invoice_number

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(ActorMixin, viewsets.ModelViewSet):
    """Customer orders."""

    queryset = Order.objects.prefetch_related("items__product").select_related(
        "sale", "created_by_admin__user", "created_by_manager__user"
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrManagerNoUpdate]
    filter_backends = [filters.SearchFilter]
    search_fields = ["order_number", "customer_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        status_param = params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        start_date = parse_day_param(params, "start_date")
        end_date = parse_day_param(params, "end_date")
        if start_date or end_date:
            queryset = queryset.filter(
                **day_range_filter("order_date", start_date, end_date)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(**role_fields(self.request.user, "created_by_"))

    def perform_destroy(self, instance):
        if instance.status == Order.Status.FULFILLED:
            raise ValidationError(
                "A fulfilled order cannot be deleted. Delete its invoice first "
                "if the sale was recorded in error."
            )
        instance.delete()

    @action(detail=False, methods=["get"])
    def summary(self, request):
        return Response(
            Order.objects.aggregate(
                total_orders=Count("id"),
                pending_orders=Count("id", filter=Q(status=Order.Status.PENDING)),
                fulfilled_orders=Count("id", filter=Q(status=Order.Status.FULFILLED)),
            )
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def fulfil(self, request, pk=None):
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
                    created_by_admin=admin_of(request.user),
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
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
