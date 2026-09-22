from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError

from .models import User
from .permissions import IsAdmin
from .serializers import UserManagementSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-only user account management (create Manager/Staff accounts, change
    role or active status, reset a password, deactivate). Full record editing
    otherwise stays in Django Admin per the project spec.

    An admin cannot lock themselves out through this endpoint: deleting your
    own account, deactivating it, or demoting it out of the Admin role is
    refused. Another admin can still do any of those to you, so the guard
    stops accidents rather than policy.
    """

    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name", "email"]

    def perform_update(self, serializer):
        instance = serializer.instance

        if instance == self.request.user:
            role = serializer.validated_data.get("role", instance.role)
            is_active = serializer.validated_data.get("is_active", instance.is_active)

            if role != User.Role.ADMIN:
                raise ValidationError(
                    {"role": "You cannot change your own account out of the Admin role."}
                )
            if not is_active:
                raise ValidationError(
                    {"is_active": "You cannot deactivate your own account."}
                )

        serializer.save()

    def perform_destroy(self, instance):
        if instance == self.request.user:
            raise ValidationError({"detail": "You cannot delete your own account."})
        instance.delete()
