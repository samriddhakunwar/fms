from typing import Callable

from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


class Staff(models.Model):
    """A factory employee. Admins and Managers are never stored here."""

    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_profile",
        limit_choices_to={"role": User.Role.STAFF},
        verbose_name="Login Account",
        help_text=(
            "The Staff login account this HR record belongs to. Linking one lets "
            "the staff member see their own profile in the app; it is optional "
            "so records can exist for staff who have no login."
        ),
    )

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
        null=True,
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
        help_text="The date the staff member started working at the factory.",
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Base Salary",
        help_text="Agreed monthly/periodic base salary for this staff member.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Employment Status",
    )

    user_id: int | None
    get_status_display: Callable[[], str]

    class Meta:
        db_table = "staff"
        verbose_name = "Staff"
        verbose_name_plural = "Staff"
        ordering = ["full_name"]

    def clean(self):
        if self.user_id and self.user.role != User.Role.STAFF:
            raise ValidationError(
                {"user": "Only a Staff account can be linked to a Staff record."}
            )

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} — {self.designation} ({self.get_status_display()})"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE
