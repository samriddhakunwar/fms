"""
employees/admin.py
==================
Admin configuration for the Employee model.

The list view is enriched with filters and a search box to help HR staff
quickly locate a particular employee.

Deletion is disabled. SalaryPayment.employee is PROTECTed to preserve the
payroll audit trail, so an employee who has ever been paid can never be
deleted. Retire them with the "Deactivate" action instead (status →
Inactive) — their payment history survives, but they are no longer offered
when recording a new salary payment.
"""

from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR

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

    actions = ("deactivate_employees", "reactivate_employees")

    # Default sort: alphabetical by full name
    ordering = ("full_name",)

    # Date drill-down based on joining date
    date_hierarchy = "joining_date"

    # ------------------------------------------------------------------
    # Deletion policy
    # ------------------------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        """
        Employees are never deleted — retire them with the Deactivate action.

        Returning False also removes the bulk "Delete selected" action, so
        nobody can walk into the ProtectedError that SalaryPayment.employee
        raises.
        """
        return False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @admin.action(description="Deactivate selected employees (soft delete)")
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(status=Employee.Status.INACTIVE)
        self.message_user(
            request,
            f"{updated} employee(s) marked Inactive. Their payment history is "
            f"kept, but they can no longer be selected for new salary payments.",
        )

    @admin.action(description="Reactivate selected employees")
    def reactivate_employees(self, request, queryset):
        updated = queryset.update(status=Employee.Status.ACTIVE)
        self.message_user(request, f"{updated} employee(s) marked Active.")

    # ------------------------------------------------------------------
    # Querysets
    # ------------------------------------------------------------------

    def get_queryset(self, request):
        """
        The full roster (active and inactive) is shown on the changelist, but
        the raw-id chooser popup used when recording a salary payment defaults
        to active employees only. An explicit ?status__exact= in the popup URL
        still wins, so former staff remain reachable.
        """
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "status__exact" not in request.GET:
            queryset = queryset.filter(status=Employee.Status.ACTIVE)
        return queryset

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
