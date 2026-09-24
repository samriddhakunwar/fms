from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # List view
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
        "role",
        "is_active",   # Filter by active / inactive accounts
        "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    # Default sort order in the changelist
    ordering = ("date_joined",)

    # Detail (add / change) view
    fieldsets = (
        *(BaseUserAdmin.fieldsets or ()),
        (
            # Section title shown in the form
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
            },
        ),
    )

    list_editable = ("role", "is_active")

    readonly_fields = ("date_joined", "last_login")

    date_hierarchy = "date_joined"
