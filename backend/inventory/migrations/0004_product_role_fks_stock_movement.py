"""
Record which Admin or Manager added / last edited each product, and log every
change to its stock level.

1. product.created_by_admin / created_by_manager and updated_by_admin /
   updated_by_manager, each pair checked so at most one is set. Existing
   products were never attributed, so they start empty.
2. New stock_movement table: one row per change to quantity_in_stock, credited
   to an admin or a manager (at most one).
3. Every existing product with stock gets one STOCK_IN "opening balance" row
   for its current quantity, so a product's movements always add up to its
   quantity_in_stock. No Admin/Manager is recorded for these rows.
"""

from django.db import migrations, models
import django.db.models.deletion


OPENING_BALANCE_REASON = "Opening balance when stock tracking began"


def log_opening_balances(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    StockMovement = apps.get_model("inventory", "StockMovement")
    StockMovement.objects.bulk_create(
        StockMovement(
            product=product,
            movement_type="STOCK_IN",
            quantity_change=product.quantity_in_stock,
            quantity_after=product.quantity_in_stock,
            reason=OPENING_BALANCE_REASON,
        )
        for product in Product.objects.filter(quantity_in_stock__gt=0)
    )


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0005_sale_created_updated_by_admin'),
        ('accounts', '0008_manager_created_by_admin_activity_log'),
        ('inventory', '0003_product_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('STOCK_IN', 'Stock In'), ('STOCK_OUT', 'Stock Out'), ('ADJUSTMENT', 'Adjustment'), ('SALE', 'Sale'), ('SALE_RETURN', 'Sale Return')], max_length=20, verbose_name='Movement Type')),
                ('quantity_change', models.IntegerField(help_text='Units added (positive) or removed (negative).', verbose_name='Quantity Change')),
                ('quantity_after', models.PositiveIntegerField(help_text='quantity_in_stock once this change was applied.', verbose_name='Quantity After')),
                ('reason', models.CharField(blank=True, max_length=255, verbose_name='Reason')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Stock Movement',
                'verbose_name_plural': 'Stock Movements',
                'db_table': 'stock_movement',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='created_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who added this product, if an Admin did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products_created', to='accounts.adminprofile', verbose_name='Created By (Admin)'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by_manager',
            field=models.ForeignKey(blank=True, help_text='The Manager who added this product, if a Manager did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products_created', to='accounts.managerprofile', verbose_name='Created By (Manager)'),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_by_admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who last edited this product, if an Admin did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products_updated', to='accounts.adminprofile', verbose_name='Last Updated By (Admin)'),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_by_manager',
            field=models.ForeignKey(blank=True, help_text='The Manager who last edited this product, if a Manager did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products_updated', to='accounts.managerprofile', verbose_name='Last Updated By (Manager)'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(('created_by_admin__isnull', True), ('created_by_manager__isnull', True), _connector='OR'), name='product_created_by_one_role'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(('updated_by_admin__isnull', True), ('updated_by_manager__isnull', True), _connector='OR'), name='product_updated_by_one_role'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='admin',
            field=models.ForeignKey(blank=True, help_text='The Admin who made this change, if an Admin did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='accounts.adminprofile', verbose_name='Admin'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='manager',
            field=models.ForeignKey(blank=True, help_text='The Manager who made this change, if a Manager did.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='accounts.managerprofile', verbose_name='Manager'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='inventory.product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='sale',
            field=models.ForeignKey(blank=True, help_text='The invoice behind a SALE movement, while it still exists.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='sales.sale', verbose_name='Sale'),
        ),
        migrations.AddConstraint(
            model_name='stockmovement',
            constraint=models.CheckConstraint(check=models.Q(('admin__isnull', True), ('manager__isnull', True), _connector='OR'), name='stock_movement_one_role'),
        ),
        # Reversing drops the table, so the rows need no separate undo.
        migrations.RunPython(log_opening_balances, migrations.RunPython.noop),
    ]
