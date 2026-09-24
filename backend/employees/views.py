from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminOrInventoryManagerReadOnly

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee HR records."""

    queryset = Employee.objects.select_related("user").all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrInventoryManagerReadOnly]
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

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        employee = Employee.objects.select_related("user").filter(
            user=request.user
        ).first()

        if employee is None:
            return Response(
                {
                    "detail": (
                        "No employee record is linked to your account yet. "
                        "Ask an administrator to link one."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self.get_serializer(employee).data)
