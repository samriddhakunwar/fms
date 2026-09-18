from rest_framework import viewsets

from accounts.permissions import IsAdmin

from .models import SalaryPayment
from .serializers import SalaryPaymentSerializer


class SalaryPaymentViewSet(viewsets.ModelViewSet):
    """
    Salary payment CRUD. Admin-only.
    """

    queryset = SalaryPayment.objects.select_related("employee").all()
    serializer_class = SalaryPaymentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get("employee")
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset
