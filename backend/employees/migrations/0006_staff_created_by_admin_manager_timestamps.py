"""
Record which Admin added each staff member, which Manager they report to,
and when the record was created / last changed.

All four columns are nullable. Existing records were never attributed, so
created_by_admin and manager start empty, and the timestamps are cleared after
the columns are added: Django fills auto_now/auto_now_add columns with the
time of the migration, which would wrongly date every existing record to today.
"""

from django.db import migrations, models
import django.db.models.deletion


def clear_backfilled_timestamps(apps, schema_editor):
    Staff = apps.get_model("employees", "Staff")
    Staff.objects.update(created_at=None, updated_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_manager_created_by_admin_activity_log'),
        ('employees', '0005_employee_to_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AddField(
            model_name='staff',
            name='created_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who added this staff record. Empty for records created before this was tracked, or if that Admin was later deleted.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff_created', to='accounts.adminprofile', verbose_name='Created By (Admin)'),
        ),
        migrations.AddField(
            model_name='staff',
            name='manager',
            field=models.ForeignKey(blank=True, help_text='The Manager this staff member reports to. Optional.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff_members', to='accounts.managerprofile', verbose_name='Reports To'),
        ),
        migrations.AddField(
            model_name='staff',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.RunPython(clear_backfilled_timestamps, migrations.RunPython.noop),
    ]
