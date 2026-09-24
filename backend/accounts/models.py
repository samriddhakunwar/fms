from typing import Callable

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INVENTORY_MANAGER = "INVENTORY_MANAGER", "Manager"
        STAFF = "STAFF", "Staff"

    # Redeclared from PermissionsMixin purely to give the auto-created
    # join tables readable names (user_group / user_permission).
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

    # Added by Django at runtime; declared here for the type checker.
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
    def is_inventory_manager(self):
        return self.role == self.Role.INVENTORY_MANAGER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
