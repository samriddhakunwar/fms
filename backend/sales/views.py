from django.db.models import Sum
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrInventoryManagerReadOnly
from fms.dates import day_range_filter, parse_day_param

from .models import Sale
from .serializers import SaleSerializer


class SaleViewSet(viewsets.ModelViewSet):
    """
    Sales (invoices). Admin records and deletes them; managers
    may read them so their panel can show the Sales Report and its charts.
    Employees have no access.

    Admin may also correct an invoice (PUT/PATCH). Rewriting the line
    items returns the old quantities to stock and re-deducts the new ones in
    one transaction, so inventory always matches what the invoice says; the
    invoice number and date stay fixed so the audit trail holds. Inventory
    Managers are barred from every write here by the permission class, not
    just by a hidden button.
    """

    queryset = Sale.objects.prefetch_related("items__product").all()
    serializer_class = SaleSerializer
    permission_classes = [IsAdminOrInventoryManagerReadOnly]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["invoice_number", "sold_to"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        date = parse_day_param(params, "date")
        start_date = parse_day_param(params, "start_date")
        end_date = parse_day_param(params, "end_date")

        if date:
            queryset = queryset.filter(**day_range_filter("sale_date", date, date))
        if start_date or end_date:
            queryset = queryset.filter(
                **day_range_filter("sale_date", start_date, end_date)
            )

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        today = timezone.localdate()
        todays_sales = Sale.objects.filter(**day_range_filter("sale_date", today, today))
        revenue = todays_sales.aggregate(total=Sum("total_amount"))["total"] or 0
        return Response(
            {
                "todays_sales": todays_sales.count(),
                "todays_revenue": revenue,
            }
        )
