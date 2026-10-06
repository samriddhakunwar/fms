"""
Credit each order to the Admin or Manager record that created it, instead of
to the login account.

Adds customer_order.created_by_admin -> admin and created_by_manager ->
manager, with a check that at most one is set. The old created_by -> user
column is kept until 0004 has copied it across.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_manager_created_by_admin_activity_log'),
        ('orders', '0002_order_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who recorded this order, if an Admin did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders_created', to='accounts.adminprofile', verbose_name='Created By (Admin)'),
        ),
        migrations.AddField(
            model_name='order',
            name='created_by_manager',
            field=models.ForeignKey(blank=True, help_text='The Manager who recorded this order, if a Manager did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders_created', to='accounts.managerprofile', verbose_name='Created By (Manager)'),
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(check=models.Q(('created_by_admin__isnull', True), ('created_by_manager__isnull', True), _connector='OR'), name='customer_order_created_by_one_role'),
        ),
    ]
