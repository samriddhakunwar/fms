"""
salary/admin.py
===============
Admin configuration for the SalaryPayment model.

The payment_date field drives both the date hierarchy navigation and the
list filter, making it easy to pull up payments for any given time period.
Employee lookups use raw_id_fields so the selector stays fast even with a
large workforce.
"""

from django.contrib import admin

from .models import SalaryPayment


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for recording and reviewing salary payments.

    Each record is effectively a ledger entry: employee → amount → method →
    date. Deleting a payment is allowed through the admin but should be done
    carefully to preserve payroll audit trails.
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    list_display = (
        "employee",       # Renders via Employee.__str__
        "amount",
        "payment_date",
        "payment_method",
    )

    # Make the employee clickable to open the change form
    list_display_links = ("employee",)

    list_filter = (
        "payment_date",    # Django built-in date hierarchy filter in sidebar
        "payment_method",  # Cash / Bank Transfer / Cheque / Mobile Banking
    )

    # Search across the employee's name and email (traverses the FK)
    search_fields = (
        "employee__full_name",  # Double underscore traverses the FK
        "employee__email",
    )

    # Most recent payments first
    ordering = ("-payment_date",)

    # Date drill-down bar at the top of the changelist
    date_hierarchy = "payment_date"

    # ------------------------------------------------------------------
    # Detail (add / change) view
    # ------------------------------------------------------------------

    # payment_date is editable (admin can correct a date if needed), but
    # we keep it visible so the default value is obvious.
    readonly_fields = ()

    fieldsets = (
        (
            "Payment Details",
            {
                "fields": (
                    "employee",
                    "amount",
                    "payment_method",
                    "payment_date",
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
