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
