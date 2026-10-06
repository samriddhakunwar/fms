"""
1. manager.created_by_admin -> admin: the Admin who created the Manager
   account. Existing managers were never attributed, so it starts empty.
2. New activity_log table: logins, logouts, failed logins and read-only views
   for all three roles, indexed by (user_id, created_at).
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_manager_role_and_admin_manager_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='managerprofile',
            name='created_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who created this Manager account. Empty for accounts created before this was tracked, or if that Admin was later deleted.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managers_created', to='accounts.adminprofile', verbose_name='Created By (Admin)'),
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, help_text="The account's role at the time, kept if the role later changes.", max_length=20, verbose_name='Role')),
                ('action', models.CharField(choices=[('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('LOGIN_FAILED', 'Login Failed'), ('VIEW', 'View')], max_length=20, verbose_name='Action')),
                ('target', models.CharField(blank=True, help_text='What was viewed, e.g. "product", "sale", "staff".', max_length=50, verbose_name='Target')),
                ('object_id', models.PositiveBigIntegerField(blank=True, help_text='The record viewed; empty for a list.', null=True, verbose_name='Object ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP Address')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('user', models.ForeignKey(blank=True, help_text='Empty for a failed login with an unknown username.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_logs', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Activity Log Entry',
                'verbose_name_plural': 'Activity Log',
                'db_table': 'activity_log',
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['user', 'created_at'], name='activity_log_user_created_idx')],
            },
        ),
    ]
