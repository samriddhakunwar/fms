from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.activity import ViewLoggingMixin
from accounts.models import ActivityLog, User
from accounts.permissions import IsAdminOrManagerReadOnly, IsStaff
from fms.actor import ActorMixin, admin_of

from .models import Staff
from .serializers import StaffSerializer


class StaffViewSet(ActorMixin, ViewLoggingMixin, viewsets.ModelViewSet):
    """Staff HR records. Admin manages them; Manager may only view."""

    queryset = Staff.objects.select_related(
        "user", "manager__user", "created_by_admin__user"
    )
    view_log_target = "staff"
    view_log_roles = (User.Role.MANAGER,)
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
        manager = self.request.query_params.get("manager")
        if manager == "me":
            queryset = queryset.filter(manager__user=self.request.user)
        elif manager:
            if not manager.isdigit():
                raise ValidationError(
                    {"manager": "manager must be a Manager id or 'me'."}
                )
            queryset = queryset.filter(manager_id=manager)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by_admin=admin_of(self.request.user))

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
        staff = self.queryset.filter(user=request.user).first()

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

        ActivityLog.record(request, ActivityLog.Action.VIEW, "staff", staff.pk)
        return Response(self.get_serializer(staff).data)
