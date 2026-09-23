"""
salary/admin.py
===============
Admin configuration for the SalaryPayment model.

Employee lookups use raw_id_fields so the selector stays fast even with a
large workforce.
"""

from django.contrib import admin

from .forms import SalaryPaymentAdminForm
from .models import SalaryPayment


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for recording and reviewing salary payments.

    Each record is effectively a ledger entry: employee → amount. Deleting a payment is allowed through the admin but should be done
    carefully to preserve payroll audit trails.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "employee",       # Renders via Employee.__str__
        "amount",
    )

    # Make the employee clickable to open the change form
    list_display_links = ("employee",)

    # Search across the employee's name and email (traverses the FK)
    search_fields = (
        "employee__full_name",  # Double underscore traverses the FK
        "employee__email",
    )

    # Most recent payments first
    ordering = ("-id",)

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    form = SalaryPaymentAdminForm  # Offers active employees only — see salary/forms.py

    fieldsets = (
        (
            "Payment Details",
            {
                "fields": (
                    "employee",
                    "amount",
                ),
            },
        ),
        (
            "Additional Notes",
            {
                "fields": ("remarks",),
                "classes": ("collapse",),  # Collapsed by default — keeps the form tidy
                "description": "Optional remarks: bonuses, advances, deductions, etc.",
            },
        ),
    )

    # Use a search popup instead of a dropdown for the employee FK.
    # This prevents the <select> widget from loading every employee at once.
    raw_id_fields = ("employee",)
