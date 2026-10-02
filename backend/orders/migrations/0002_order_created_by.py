"""
Record which Admin or Manager account created each order.

Nullable with SET_NULL so deleting an account never blocks on its orders
(the reason sales/0003 dropped Sale.sold_by). Orders that already exist were
never attributed, so they are left empty rather than guessed.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0007_manager_role_and_admin_manager_tables"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The Admin or Manager account that recorded this order. Empty "
                    "for orders created before this was tracked, or if that account "
                    "was later deleted."
                ),
                limit_choices_to={"role__in": ["ADMIN", "MANAGER"]},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Created By",
            ),
        ),
    ]
