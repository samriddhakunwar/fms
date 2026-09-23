from django.db import migrations, models


def employee_to_staff(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="EMPLOYEE").update(role="STAFF")


def staff_to_employee(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="STAFF").update(role="EMPLOYEE")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_rename_stale_fk_constraints"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Admin"),
                    ("INVENTORY_MANAGER", "Manager"),
                    ("STAFF", "Staff"),
                ],
                default="ADMIN",
                max_length=20,
            ),
        ),
        migrations.RunPython(employee_to_staff, staff_to_employee),
    ]
