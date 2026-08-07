"""
accounts/admin.py
=================
Admin configuration for the custom User model.

Extends Django's built-in UserAdmin so that all default fields
(password management, permissions, groups, etc.) are preserved,
while adding our custom `role` and `phone_number` fields.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.

    Inherits all default UserAdmin behaviour (password hashing,
    permission management, etc.) and layers on the project-specific
    `role` and `phone_number` fields.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    # Columns shown in the changelist table
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "date_joined",
    )

    # Sidebar filters in the changelist
    list_filter = (
        "role",        # Filter by Admin / Inventory Manager / Employee
        "is_active",   # Filter by active / inactive accounts
        "is_staff",
    )

    # Fields that can be searched via the search box
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    # Default sort order in the changelist
    ordering = ("date_joined",)

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    # Extend the default fieldsets with our custom fields.
    # BaseUserAdmin.fieldsets already contains the standard Django sections;
    # we inject the project-specific section right after the first block.
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            # Section title shown in the form
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
            },
        ),
    )

    # Fields shown on the *add* (create) form.
    # BaseUserAdmin.add_fieldsets handles username/password; we add role.
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
            },
        ),
    )

    # Fields the admin can edit directly in the list view (inline editing)
    list_editable = ("role", "is_active")

    # Fields that are shown but cannot be edited (auto-managed by Django)
    readonly_fields = ("date_joined", "last_login")

    # Quick navigation by join date using a date drill-down
    date_hierarchy = "date_joined"
