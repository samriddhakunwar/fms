"""
Turn the `employee` table into the `staff` table.

The table is renamed in place (RenameModel + AlterModelTable) rather than
copied, so every row keeps its id, its HR data and its user_id link, and the
foreign key to `user` is carried over untouched.

Then the data is made to fit the new rule that only Staff live here:

* A record linked to an ADMIN or MANAGER account is not Staff. Its account
  gets its Admin/Manager row (normally already created by accounts/0007), any
  name/email/phone the account is missing is copied across from the record,
  and the record is removed from `staff`. Each one is listed in the migration
  output. (The live database had none at the time of writing.)
* A STAFF account with no record gets one, so every Staff login has a
  profile to show. The HR fields it cannot know are filled with neutral
  placeholders for an Admin to correct.

Records with no login are ordinary Staff and are left as they are.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

PLACEHOLDER_DESIGNATION = "Unassigned"


def split_non_staff_records(apps, schema_editor):
    Staff = apps.get_model("employees", "Staff")
    User = apps.get_model("accounts", "User")
    AdminProfile = apps.get_model("accounts", "AdminProfile")
    ManagerProfile = apps.get_model("accounts", "ManagerProfile")
    profile_for = {"ADMIN": AdminProfile, "MANAGER": ManagerProfile}

    misplaced = Staff.objects.select_related("user").filter(
        user__role__in=list(profile_for)
    )
    for record in misplaced:
        user = record.user
        profile_for[user.role].objects.get_or_create(user=user)

        first_name, _, last_name = record.full_name.partition(" ")
        updates = {
            "first_name": user.first_name or first_name,
            "last_name": user.last_name or last_name,
            "email": user.email or record.email or "",
            "phone_number": user.phone_number or record.phone,
        }
        User.objects.filter(pk=user.pk).update(**updates)

        print(
            f"\n  moved employee #{record.pk} '{record.full_name}' "
            f"({record.designation}) out of staff: account '{user.username}' "
            f"is {user.role}"
        )
        record.delete()

    for user in User.objects.filter(role="STAFF", staff_profile__isnull=True):
        Staff.objects.create(
            user=user,
            full_name=f"{user.first_name} {user.last_name}".strip() or user.username,
            email=user.email or None,
            phone=user.phone_number,
            designation=PLACEHOLDER_DESIGNATION,
            joining_date=user.date_joined.date(),
            salary=0,
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0007_manager_role_and_admin_manager_tables"),
        ("employees", "0004_employee_email_nullable"),
    ]

    operations = [
        migrations.RenameModel(old_name="Employee", new_name="Staff"),
        migrations.AlterModelOptions(
            name="staff",
            options={
                "ordering": ["full_name"],
                "verbose_name": "Staff",
                "verbose_name_plural": "Staff",
            },
        ),
        migrations.AlterModelTable(name="staff", table="staff"),
        migrations.AlterField(
            model_name="staff",
            name="user",
            field=models.OneToOneField(
                blank=True,
                help_text=(
                    "The Staff login account this HR record belongs to. Linking one "
                    "lets the staff member see their own profile in the app; it is "
                    "optional so records can exist for staff who have no login."
                ),
                limit_choices_to={"role": "STAFF"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="staff_profile",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Login Account",
            ),
        ),
        migrations.AlterField(
            model_name="staff",
            name="joining_date",
            field=models.DateField(
                help_text="The date the staff member started working at the factory.",
                verbose_name="Joining Date",
            ),
        ),
        migrations.AlterField(
            model_name="staff",
            name="salary",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Agreed monthly/periodic base salary for this staff member.",
                max_digits=12,
                verbose_name="Base Salary",
            ),
        ),
        # Removed records cannot be rebuilt on the way back; the table rename
        # itself reverses cleanly.
        migrations.RunPython(split_non_staff_records, migrations.RunPython.noop),
    ]
