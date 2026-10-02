from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrManagerReadOnly, IsStaff

from .models import Staff
from .serializers import StaffSerializer


class StaffViewSet(viewsets.ModelViewSet):
    """Staff HR records. Admin manages them; Manager may only view."""

    queryset = Staff.objects.select_related("user").all()
    serializer_class = StaffSerializer
    permission_classes = [IsAdminOrManagerReadOnly]
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
        return Response({"total_staff": Staff.objects.count()})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsStaff],
        url_path="me",
    )
    def me(self, request):
        # Always looked up from the session user, never from an id in the URL.
        staff = Staff.objects.select_related("user").filter(user=request.user).first()

        if staff is None:
            return Response(
                {
                    "detail": (
                        "No staff record is linked to your account yet. "
                        "Ask an administrator to link one."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self.get_serializer(staff).data)
