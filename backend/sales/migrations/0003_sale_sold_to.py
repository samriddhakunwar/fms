"""
Replace Sale.sold_by (FK to the system user who recorded the invoice) with
Sale.sold_to (the customer the invoice was issued to).

The factory does not track which staff member entered a sale, so the FK was
both unused and the last remaining PROTECT reference to accounts.User — it
made deleting a user who had ever recorded a sale impossible.

Existing rows are backfilled before the column is added as NOT NULL: the
seeded demo invoices get the customers listed in accounts/seed_data.py, and
anything else falls back to "Walk-in Customer" so no invoice is left blank.
Edit them in the admin if a different customer is correct.
"""

from django.db import migrations, models

# Mirrors the customers in accounts/management/commands/seed_data.py
SEEDED_CUSTOMERS = {
    "INV-2026-0001": "Shyam Pvt. Ltd.",
    "INV-2026-0002": "Himalaya Trading Concern",
    "INV-2026-0003": "Sita Hardware Suppliers",
    "INV-2026-0004": "Gorkha Construction Pvt. Ltd.",
    "INV-2026-0005": "Annapurna Steel Udhyog",
}

FALLBACK = "Walk-in Customer"


def backfill(apps, schema_editor):
    Sale = apps.get_model("sales", "Sale")
    for sale in Sale.objects.all():
        sale.sold_to = SEEDED_CUSTOMERS.get(sale.invoice_number, FALLBACK)
        sale.save(update_fields=["sold_to"])


def unbackfill(apps, schema_editor):
    # sold_to is dropped on the way back, so there is nothing to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0002_alter_sale_table_alter_saleitem_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="sale",
            name="sold_to",
            field=models.CharField(
                default="",
                help_text="The customer or company this invoice was issued to.",
                max_length=255,
                verbose_name="Sold To",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(backfill, unbackfill),
        migrations.RemoveField(
            model_name="sale",
            name="sold_by",
        ),
    ]
