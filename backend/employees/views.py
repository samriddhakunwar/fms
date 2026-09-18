from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdmin

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee HR-record CRUD. Admin-only — matches the role matrix (Inventory
    Managers and Employees have no employee-management access).
    """

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        designation = self.request.query_params.get("designation")
        if designation:
            queryset = queryset.filter(designation__iexact=designation)
        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        return Response({"total_employees": Employee.objects.count()})
