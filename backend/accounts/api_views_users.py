from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError

from fms.actor import admin_of

from .models import User
from .permissions import IsAdmin
from .serializers import (
    AdminAccountSerializer,
    ManagerAccountSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Every login account, read-only. Accounts are created and changed through
    /admins/, /managers/ and /staff/ so each one lands in the right table.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name", "email"]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role.upper())
        return queryset


class RoleAccountViewSet(viewsets.ModelViewSet):
    role_value: str = ""
    profile_attr: str = ""
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name", "email"]

    def get_queryset(self):
        return User.objects.filter(role=self.role_value).select_related(
            self.profile_attr
        )


class AdminAccountViewSet(RoleAccountViewSet):
    """Admin accounts (`user` + `admin`)."""

    role_value = User.Role.ADMIN
    profile_attr = "admin_profile"
    serializer_class = AdminAccountSerializer

    def perform_update(self, serializer):
        instance = serializer.instance
        is_active = serializer.validated_data.get("is_active", instance.is_active)
        if instance == self.request.user and not is_active:
            raise ValidationError({"is_active": "You cannot deactivate your own account."})
        serializer.save()

    def perform_destroy(self, instance):
        if instance == self.request.user:
            raise ValidationError({"detail": "You cannot delete your own account."})
        # Deleting the login cascades to its Admin row.
        super().perform_destroy(instance)


class ManagerAccountViewSet(RoleAccountViewSet):
    """Manager accounts (`user` + `manager`)."""

    role_value = User.Role.MANAGER
    profile_attr = "manager_profile"
    serializer_class = ManagerAccountSerializer

    def get_queryset(self):
        return super().get_queryset().select_related("manager_profile__created_by_admin__user")

    def perform_create(self, serializer):
        user = serializer.save()
        profile = user.manager_profile  # created by the post_save signal
        profile.created_by_admin = admin_of(self.request.user)
        profile.save(update_fields=["created_by_admin"])
