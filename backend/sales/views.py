from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrManagerReadOnly
from accounts.activity import ViewLoggingMixin
from accounts.models import User
from fms.actor import ActorMixin, admin_of
from fms.dates import day_range_filter, parse_day_param

from .models import Sale
from .serializers import SaleSerializer


class SaleViewSet(ActorMixin, ViewLoggingMixin, viewsets.ModelViewSet):
    queryset = Sale.objects.prefetch_related("items__product").select_related(
        "order", "created_by_admin__user", "updated_by_admin__user"
    )
    view_log_target = "sale"
    view_log_roles = (User.Role.MANAGER,)
    serializer_class = SaleSerializer
    permission_classes = [IsAdminOrManagerReadOnly]
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

    def perform_create(self, serializer):
        serializer.save(created_by_admin=admin_of(self.request.user))

    def perform_update(self, serializer):
        serializer.save(updated_by_admin=admin_of(self.request.user))

    @action(detail=False, methods=["get"])
    def summary(self, request):
        today = timezone.localdate()
        totals = Sale.objects.filter(**day_range_filter("sale_date", today, today)).aggregate(
            count=Count("id"), revenue=Sum("total_amount")
        )
        return Response(
            {"todays_sales": totals["count"], "todays_revenue": totals["revenue"] or 0}
        )
