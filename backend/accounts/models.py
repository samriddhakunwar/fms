import logging
from typing import Callable

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models, transaction

logger = logging.getLogger(__name__)


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
    created_by_admin = models.ForeignKey(
        AdminProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managers_created",
        verbose_name="Created By (Admin)",
        help_text=(
            "The Admin who created this Manager account. Empty for accounts "
            "created before this was tracked, or if that Admin was later deleted."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    user_id: int
    created_by_admin_id: int | None

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


class ActivityLog(models.Model):
    """
    Logins, logouts and read-only views, for every role. Rows are written by
    the API and never edited; writing one never fails the request.
    """

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
        VIEW = "VIEW", "View"

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
        verbose_name="User",
        help_text="Empty for a failed login with an unknown username.",
    )
    role = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Role",
        help_text="The account's role at the time, kept if the role later changes.",
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name="Action",
    )
    target = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Target",
        help_text='What was viewed, e.g. "product", "sale", "staff".',
    )
    object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Object ID",
        help_text="The record viewed; empty for a list.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    get_action_display: Callable[[], str]

    class Meta:
        db_table = "activity_log"
        verbose_name = "Activity Log Entry"
        verbose_name_plural = "Activity Log"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="activity_log_user_created_idx"),
        ]

    def __str__(self):
        who = self.user.username if self.user_id else "unknown"
        what = f" {self.target}" if self.target else ""
        return f"{who} {self.get_action_display()}{what} ({self.created_at:%Y-%m-%d %H:%M})"

    @classmethod
    def record(cls, request, action, target="", object_id=None, user=None):
        """
        Log an action for request.user (or the given user). Swallows any error
        so logging can never break the request it describes.
        """
        try:
            if user is None:
                user = getattr(request, "user", None)
            if user is not None and not user.is_authenticated:
                user = None
            meta = getattr(request, "META", {})
            with transaction.atomic():
                return cls.objects.create(
                    user=user,
                    role=user.role if user else "",
                    action=action,
                    target=target,
                    object_id=object_id,
                    ip_address=meta.get("REMOTE_ADDR") or None,
                )
        except Exception:  # noqa: BLE001 — logging must never fail the request
            logger.exception("Could not write activity log entry (%s %s)", action, target)
            return None
