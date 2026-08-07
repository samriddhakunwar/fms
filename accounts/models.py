from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INVENTORY_MANAGER = "INVENTORY_MANAGER", "Inventory Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"

    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
    )

    class Meta:
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
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE
