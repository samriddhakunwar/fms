"""
Record which Admin recorded and last edited each sale. Only Admins change
sales (Managers are view-only), so there is no Manager column. Existing sales
were never attributed, so both start empty.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_manager_created_by_admin_activity_log'),
        ('sales', '0004_sale_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='created_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who recorded this sale. Empty for sales recorded before this was tracked, or if that Admin was later deleted.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_created', to='accounts.adminprofile', verbose_name='Recorded By (Admin)'),
        ),
        migrations.AddField(
            model_name='sale',
            name='updated_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who last edited this sale.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_updated', to='accounts.adminprofile', verbose_name='Last Updated By (Admin)'),
        ),
    ]
