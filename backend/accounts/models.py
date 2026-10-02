from typing import Callable

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        STAFF = "STAFF", "Staff"

    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text=(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="user_set",
        related_query_name="user",
        db_table="user_group",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="user_set",
        related_query_name="user",
        db_table="user_permission",
    )

    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
    )

    get_role_display: Callable[[], str]

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username}) — {self.get_role_display()}"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def clean(self):
        super().clean()
        # A linked Staff record is the person's HR file; moving the account to
        # another role would leave an Admin/Manager sitting in the Staff table.
        if self.pk and self.role != self.Role.STAFF:
            from employees.models import Staff

            if Staff.objects.filter(user_id=self.pk).exists():
                raise ValidationError(
                    {
                        "role": (
                            "This account is linked to a Staff record. Unlink it "
                            "from the Staff record before changing its role."
                        )
                    }
                )


class AdminProfile(models.Model):
    """The Admin record for a login account whose role is ADMIN."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        limit_choices_to={"role": User.Role.ADMIN},
        verbose_name="Login Account",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    user_id: int

    class Meta:
        db_table = "admin"
        verbose_name = "Admin"
        verbose_name_plural = "Admins"
        ordering = ["user__username"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        if self.user_id and self.user.role != User.Role.ADMIN:
            raise ValidationError({"user": "Only an Admin account can have an Admin record."})


class ManagerProfile(models.Model):
    """The Manager record for a login account whose role is MANAGER."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="manager_profile",
        limit_choices_to={"role": User.Role.MANAGER},
        verbose_name="Login Account",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    user_id: int

    class Meta:
        db_table = "manager"
        verbose_name = "Manager"
        verbose_name_plural = "Managers"
        ordering = ["user__username"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        if self.user_id and self.user.role != User.Role.MANAGER:
            raise ValidationError(
                {"user": "Only a Manager account can have a Manager record."}
            )


PROFILE_MODEL_FOR_ROLE = {
    User.Role.ADMIN: AdminProfile,
    User.Role.MANAGER: ManagerProfile,
}


def sync_role_profile(user):
    """Give the account exactly the Admin/Manager record its role calls for."""
    for role, model in PROFILE_MODEL_FOR_ROLE.items():
        if user.role == role:
            model.objects.get_or_create(user=user)
        else:
            model.objects.filter(user=user).delete()
