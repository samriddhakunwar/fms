from django.db import models
from django.utils import timezone


class SalaryPayment(models.Model):


    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        CHEQUE = "CHEQUE", "Cheque"
        MOBILE_BANKING = "MOBILE_BANKING", "Mobile Banking"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="salary_payments",
        verbose_name="Employee",
        help_text="The employee who received this payment.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount Paid",
        help_text="The actual amount disbursed in this payment.",
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Payment Date",
        help_text="Date and time when the payment was processed.",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="Payment Method",
    )
    remarks = models.TextField(
        blank=True,
        verbose_name="Remarks",
        help_text="Optional notes about this payment (e.g. bonus, advance, deduction reason).",
    )

    class Meta:
        verbose_name = "Salary Payment"
        verbose_name_plural = "Salary Payments"
        ordering = ["-payment_date"]

    def __str__(self):
        return (
            f"{self.employee.full_name} — "
            f"{self.amount} via {self.get_payment_method_display()} "
            f"on {self.payment_date.strftime('%Y-%m-%d')}"
        )
