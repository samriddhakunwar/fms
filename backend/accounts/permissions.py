from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import User


class IsAdmin(BasePermission):
    message = "Only Admin users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )


class IsInventoryManager(BasePermission):
    message = "Only manager users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.INVENTORY_MANAGER
        )


class IsStaff(BasePermission):
    message = "Only Staff users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.STAFF
        )


class IsAdminOrInventoryManager(BasePermission):
    message = "Only Admin or manager users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMIN, User.Role.INVENTORY_MANAGER)
        )


class IsAdminOrInventoryManagerOrStaffReadOnly(BasePermission):
    message = "Staff may only view inventory, not change it."

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        if user.role in (User.Role.ADMIN, User.Role.INVENTORY_MANAGER):
            return True

        return user.role == User.Role.STAFF and request.method in SAFE_METHODS


class IsAdminOrInventoryManagerReadOnly(BasePermission):
    message = "Managers may only view sales, not change them."

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        if user.role == User.Role.ADMIN:
            return True

        return (
            user.role == User.Role.INVENTORY_MANAGER
            and request.method in SAFE_METHODS
        )


class IsAdminOrInventoryManagerNoUpdate(BasePermission):
    message = "Managers may not update orders."

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        if user.role == User.Role.ADMIN:
            return True

        return (
            user.role == User.Role.INVENTORY_MANAGER
            and request.method not in ("PUT", "PATCH")
        )
