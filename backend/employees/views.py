from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminOrInventoryManagerReadOnly

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee HR records.

    ADMIN has full CRUD. INVENTORY_MANAGER is read-only — managers need to see
    staff records but must not change them. STAFF cannot reach the list or
    any record by id; the one thing they can read is their own profile, via
    the ``me`` action below.
    """

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
        """
        The caller's own HR record, looked up from the session user.

        There is no id in the URL by design: the record is resolved from
        ``request.user`` alone, so an employee cannot reach a colleague's
        profile by editing an id — the detail route stays closed to them.
        """
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
