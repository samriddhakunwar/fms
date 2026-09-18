"""
accounts/permissions.py
========================
Reusable DRF permission classes enforcing the three FMS roles at the API
layer. React route guards are UI convenience only — these are the real
authorization boundary and must be attached to every future endpoint that
is role-restricted.
"""

from rest_framework.permissions import BasePermission

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
    message = "Only Inventory Manager users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.INVENTORY_MANAGER
        )


class IsEmployee(BasePermission):
    message = "Only Employee users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.EMPLOYEE
        )


class IsAdminOrInventoryManager(BasePermission):
    message = "Only Admin or Inventory Manager users may perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.ADMIN, User.Role.INVENTORY_MANAGER)
        )
