from django.db.models import Sum
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdmin

from .models import Sale
from .serializers import SaleSerializer


class SaleViewSet(viewsets.ModelViewSet):
    """
    Sales (invoices). Admin-only, matching the role matrix — only Admin
    records/views sales.

    No update endpoint: an invoice is either correct or it should be
    deleted (which restores stock via the SaleItem pre_delete signal) and
    re-created. This avoids the ambiguity of editing line items after the
    fact silently mutating inventory.
    """

    queryset = Sale.objects.prefetch_related("items__product").all()
    serializer_class = SaleSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "post", "delete", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["invoice_number", "sold_to"]

    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get("date")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if date:
            queryset = queryset.filter(sale_date__date=date)
        if start_date:
            queryset = queryset.filter(sale_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sale_date__date__lte=end_date)

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        today = timezone.localdate()
        todays_sales = Sale.objects.filter(sale_date__date=today)
        revenue = todays_sales.aggregate(total=Sum("total_amount"))["total"] or 0
        return Response(
            {
                "todays_sales": todays_sales.count(),
                "todays_revenue": revenue,
            }
        )
