"""
employees/admin.py
==================
Admin configuration for the Employee model.

Full CRUD is available through Django's standard add / change / delete views.
The list view is enriched with filters and a search box to help HR staff
quickly locate a particular employee.
"""

from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin interface for the Employee model.

    Provides search, status / designation filtering, and date-based
    navigation so administrators can maintain employee records efficiently.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "full_name",
        "designation",
        "email",
        "phone",
        "salary",
        "status",
        "joining_date",
    )

    # Make the name a clickable link to the change form
    list_display_links = ("full_name",)

    # Allow quick in-list editing of status without opening the change form
    list_editable = ("status",)

    list_filter = (
        "status",       # Active / Inactive
        "designation",  # Job title / role within the factory
    )

    search_fields = (
        "full_name",    # Search by employee name
        "email",        # Search by email address
        "designation",  # Search by job title
    )

    # Default sort: alphabetical by full name
    ordering = ("full_name",)

    # Date drill-down based on joining date
    date_hierarchy = "joining_date"

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "address",
                ),
            },
        ),
        (
            "Employment Details",
            {
                "fields": (
                    "designation",
                    "joining_date",
                    "salary",
                    "status",
                ),
            },
        ),
    )
