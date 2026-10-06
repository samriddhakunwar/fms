"""
Move customer_order.created_by (-> user) into the role columns added in 0003,
then drop it.

Each order goes by its creator's role:
* ADMIN account   -> created_by_admin   = that account's admin row
* MANAGER account -> created_by_manager = that account's manager row
* anything else (no creator, a STAFF account, or an account missing its role
  row) -> both left empty, and listed in the migration output.

Reversible: going back re-adds created_by and fills it from whichever role
column is set.
"""

from django.db import migrations


def copy_to_role_columns(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    AdminProfile = apps.get_model("accounts", "AdminProfile")
    ManagerProfile = apps.get_model("accounts", "ManagerProfile")

    admin_for = dict(AdminProfile.objects.values_list("user_id", "pk"))
    manager_for = dict(ManagerProfile.objects.values_list("user_id", "pk"))

    orders = Order.objects.select_related("created_by").exclude(created_by=None)
    for order in orders:
        user = order.created_by
        if user.role == "ADMIN" and user.pk in admin_for:
            order.created_by_admin_id = admin_for[user.pk]
        elif user.role == "MANAGER" and user.pk in manager_for:
            order.created_by_manager_id = manager_for[user.pk]
        else:
            print(
                f"\n  order {order.order_number}: creator '{user.username}' "
                f"({user.role}) has no admin/manager row; left unattributed"
            )
            continue
        order.save(update_fields=["created_by_admin", "created_by_manager"])


def copy_back_to_user(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    orders = Order.objects.select_related("created_by_admin", "created_by_manager")
    for order in orders:
        profile = order.created_by_admin or order.created_by_manager
        if profile is not None:
            order.created_by_id = profile.user_id
            order.save(update_fields=["created_by"])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_created_by_admin_manager'),
    ]

    operations = [
        migrations.RunPython(copy_to_role_columns, copy_back_to_user),
        migrations.RemoveField(
            model_name='order',
            name='created_by',
        ),
    ]
