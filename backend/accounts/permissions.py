"""
accounts/permissions.py
========================
Reusable DRF permission classes enforcing the three FMS roles at the API
layer. React route guards are UI convenience only — these are the real
authorization boundary and must be attached to every future endpoint that
is role-restricted.
"""

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


class IsAdminOrInventoryManagerOrEmployeeReadOnly(BasePermission):
    """
    Admin and Inventory Manager get full CRUD. Employees may read only —
    they need to see what is in stock, but must not add, update or delete
    items. Anonymous users get nothing.
    """

    message = "Employees may only view inventory, not change it."

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        if user.role in (User.Role.ADMIN, User.Role.INVENTORY_MANAGER):
            return True

        return user.role == User.Role.EMPLOYEE and request.method in SAFE_METHODS


class IsAdminOrInventoryManagerReadOnly(BasePermission):
    """
    Admin gets full CRUD. Inventory Manager may read only.

    Used by the sales endpoints so Inventory Managers can view the Sales
    Report and its charts without being able to record or delete an
    invoice. Employees get nothing here — sales figures are not theirs.
    """

    message = "Inventory Managers may only view sales, not change them."

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
