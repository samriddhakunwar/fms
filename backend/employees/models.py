from django.db import models


class Employee(models.Model):
    """
    Represents a factory employee.

    Tracks personal details, employment information, and payroll data.
    The salary field here stores the agreed/base salary. Actual payments
    are recorded separately in the SalaryPayment model.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    full_name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        verbose_name="Email Address",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Phone Number",
    )
    address = models.TextField(
        blank=True,
        verbose_name="Address",
    )
    designation = models.CharField(
        max_length=100,
        verbose_name="Designation",
        help_text="Job title or role within the factory (e.g. Machine Operator).",
    )
    joining_date = models.DateField(
        verbose_name="Joining Date",
        help_text="The date the employee started working at the factory.",
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Base Salary",
        help_text="Agreed monthly/periodic base salary for this employee.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Employment Status",
    )

    class Meta:
        db_table = "employee"
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} — {self.designation} ({self.get_status_display()})"

    @property
    def is_active(self) -> bool:
        """Returns True if the employee is currently active."""
        return self.status == self.Status.ACTIVE
