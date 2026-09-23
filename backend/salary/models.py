from django.db import models


class SalaryPayment(models.Model):
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
    remarks = models.TextField(
        blank=True,
        verbose_name="Remarks",
        help_text="Optional notes about this payment (e.g. bonus, advance, deduction reason).",
    )

    class Meta:
        db_table = "salary_payment"
        verbose_name = "Salary Payment"
        verbose_name_plural = "Salary Payments"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.amount}"
