"""
Converge FK constraint/index names with the table renames in 0004 and the
matching migrations in employees/inventory/sales.

MySQL's RENAME TABLE leaves constraints on *other* tables untouched, so a
database migrated in place keeps names like
`sales_sale_sold_by_id_..._fk_accounts_user_id`, while a database built by a
fresh `migrate` derives `..._fk_user_id` from the new table name. Without this
step the two diverge and database_schema.sql can only describe one of them.

Each rename is applied only when the stale name is actually present, so this
is a no-op on a freshly migrated database.
"""

from django.db import migrations

# (table, column, old constraint name, new constraint name, referenced table)
RENAMES = [
    (
        "django_admin_log",
        "user_id",
        "django_admin_log_user_id_c564eba6_fk_accounts_user_id",
        "django_admin_log_user_id_c564eba6_fk_user_id",
        "user",
    ),
    (
        "sale",
        "sold_by_id",
        "sales_sale_sold_by_id_c69f0cbe_fk_accounts_user_id",
        "sales_sale_sold_by_id_c69f0cbe_fk_user_id",
        "user",
    ),
    (
        "sale_item",
        "product_id",
        "sales_saleitem_product_id_aeb6c9cd_fk_inventory_product_id",
        "sales_saleitem_product_id_aeb6c9cd_fk_product_id",
        "product",
    ),
]


def _constraint_exists(cursor, table, name):
    cursor.execute(
        """
        SELECT 1
          FROM information_schema.table_constraints
         WHERE constraint_schema = DATABASE()
           AND table_name = %s
           AND constraint_name = %s
        """,
        [table, name],
    )
    return cursor.fetchone() is not None


def _rename(cursor, table, column, old, new, references):
    # MySQL cannot rename a foreign key in place: drop it, rename the index
    # that backs it, then re-add the constraint under the new name.
    cursor.execute("ALTER TABLE `%s` DROP FOREIGN KEY `%s`" % (table, old))
    cursor.execute(
        "ALTER TABLE `%s` RENAME INDEX `%s` TO `%s`" % (table, old, new)
    )
    cursor.execute(
        "ALTER TABLE `%s` ADD CONSTRAINT `%s` FOREIGN KEY (`%s`) "
        "REFERENCES `%s` (`id`)" % (table, new, column, references)
    )


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table, column, old, new, references in RENAMES:
            if _constraint_exists(cursor, table, old):
                _rename(cursor, table, column, old, new, references)


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for table, column, old, new, references in RENAMES:
            if _constraint_exists(cursor, table, new):
                _rename(cursor, table, column, new, old, references)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_user_groups_alter_user_user_permissions_and_more"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("employees", "0002_alter_employee_table"),
        ("inventory", "0002_alter_product_table"),
        ("sales", "0002_alter_sale_table_alter_saleitem_table"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
