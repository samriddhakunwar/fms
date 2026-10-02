"""
Split Admin and Manager accounts into their own tables.

1. The INVENTORY_MANAGER role value becomes MANAGER, so login now reports
   {"role": "MANAGER"}.
2. New `admin` and `manager` tables, each one-to-one with `user`.
3. Every existing ADMIN / MANAGER account gets its row in the matching table.
   Passwords, usernames and user ids are untouched — the `user` table remains
   the single login table.

Staff accounts are handled by employees/0005, which turns the old `employee`
table into `staff`.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def rename_manager_role(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="INVENTORY_MANAGER").update(role="MANAGER")


def restore_manager_role(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="MANAGER").update(role="INVENTORY_MANAGER")


def create_role_rows(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    AdminProfile = apps.get_model("accounts", "AdminProfile")
    ManagerProfile = apps.get_model("accounts", "ManagerProfile")

    for user in User.objects.filter(role="ADMIN"):
        AdminProfile.objects.get_or_create(user=user)
    for user in User.objects.filter(role="MANAGER"):
        ManagerProfile.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_rename_employee_role_to_staff"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("ADMIN", "Admin"), ("MANAGER", "Manager"), ("STAFF", "Staff")],
                default="ADMIN",
                max_length=20,
            ),
        ),
        migrations.RunPython(rename_manager_role, restore_manager_role),
        migrations.CreateModel(
            name="AdminProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "ADMIN"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="admin_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Login Account",
                    ),
                ),
            ],
            options={
                "verbose_name": "Admin",
                "verbose_name_plural": "Admins",
                "db_table": "admin",
                "ordering": ["user__username"],
            },
        ),
        migrations.CreateModel(
            name="ManagerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "MANAGER"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manager_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Login Account",
                    ),
                ),
            ],
            options={
                "verbose_name": "Manager",
                "verbose_name_plural": "Managers",
                "db_table": "manager",
                "ordering": ["user__username"],
            },
        ),
        # Reversing drops both tables, so the rows need no separate undo.
        migrations.RunPython(create_role_rows, migrations.RunPython.noop),
    ]
