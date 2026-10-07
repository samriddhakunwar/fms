from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import User


def _role(request):
    user = request.user
    if not (user and user.is_authenticated):
        return None
    return user.role


class IsAdmin(BasePermission):
    message = "Only Admin users may perform this action."

    def has_permission(self, request, view):
        return _role(request) == User.Role.ADMIN


class IsStaff(BasePermission):
    message = "Only Staff users may perform this action."

    def has_permission(self, request, view):
        return _role(request) == User.Role.STAFF


class IsAdminOrManager(BasePermission):
    message = "Only Admin or Manager users may perform this action."

    def has_permission(self, request, view):
        return _role(request) in (User.Role.ADMIN, User.Role.MANAGER)


class IsAdminOrManagerOrStaffReadOnly(BasePermission):
    message = "Staff may only view inventory, not change it."

    def has_permission(self, request, view):
        role = _role(request)
        if role in (User.Role.ADMIN, User.Role.MANAGER):
            return True
        return role == User.Role.STAFF and request.method in SAFE_METHODS


class IsAdminOrManagerReadOnly(BasePermission):
    message = "Managers may only view this, not change it."

    def has_permission(self, request, view):
        role = _role(request)
        if role == User.Role.ADMIN:
            return True
        return role == User.Role.MANAGER and request.method in SAFE_METHODS


class IsAdminOrManagerNoUpdate(BasePermission):
    message = "Managers may not update orders."

    def has_permission(self, request, view):
        role = _role(request)
        if role == User.Role.ADMIN:
            return True
        return role == User.Role.MANAGER and request.method not in ("PUT", "PATCH")
