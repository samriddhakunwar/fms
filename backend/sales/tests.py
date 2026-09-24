# DRF ships no type stubs, so the checker sees test-client responses as plain
# HttpResponse (no .data) and can't see Django's auto fields (.id, reverse
# relations). Those attributes exist at runtime.
# pyright: reportAttributeAccessIssue=false

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import Product

from .models import Sale, SaleItem


class SaleApiTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.employee = User.objects.create_user(
            username="employee_user",
            password=self.password,
            role=User.Role.STAFF,
        )
        self.chair = Product.objects.create(
            product_name="Chair",
            sku="SKU-CHAIR",
            selling_price=Decimal("500.00"),
            quantity_in_stock=50,
            minimum_stock_level=10,
        )
        self.table = Product.objects.create(
            product_name="Table",
            sku="SKU-TABLE",
            selling_price=Decimal("2000.00"),
            quantity_in_stock=10,
            minimum_stock_level=2,
        )

    def _login_admin(self):
        self.client.login(username="admin_user", password=self.password)

    def test_employee_cannot_record_sale(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.post(
            reverse("sale-list"),
            {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 5}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_successful_sale_deducts_stock_and_computes_total(self):
        self._login_admin()
        payload = {
            "sold_to": "Shyam Pvt. Ltd.",
            "items_input": [
                {"product": self.chair.id, "quantity": 5},
                {"product": self.table.id, "quantity": 2},
            ]
        }
        response = self.client.post(reverse("sale-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.chair.refresh_from_db()
        self.table.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 45)
        self.assertEqual(self.table.quantity_in_stock, 8)

        expected_total = Decimal("500.00") * 5 + Decimal("2000.00") * 2
        self.assertEqual(Decimal(response.data["total_amount"]), expected_total)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertTrue(response.data["invoice_number"].startswith("INV-"))

    def test_insufficient_stock_rejects_entire_sale(self):
        self._login_admin()
        payload = {
            "sold_to": "Shyam Pvt. Ltd.",
            "items_input": [
                {"product": self.chair.id, "quantity": 5},
                {"product": self.table.id, "quantity": 999},  # more than available
            ]
        }
        response = self.client.post(reverse("sale-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Nothing should have been deducted — the whole sale rolled back.
        self.chair.refresh_from_db()
        self.table.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 50)
        self.assertEqual(self.table.quantity_in_stock, 10)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleItem.objects.count(), 0)

    def test_deleting_sale_restores_stock(self):
        self._login_admin()
        payload = {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 5}]}
        create_response = self.client.post(reverse("sale-list"), payload, format="json")
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 45)

        sale_id = create_response.data["id"]
        delete_response = self.client.delete(reverse("sale-detail", args=[sale_id]))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 50)
        self.assertEqual(SaleItem.objects.count(), 0)

    def test_editing_sale_item_quantity_only_adjusts_delta(self):
        self._login_admin()
        payload = {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 5}]}
        create_response = self.client.post(reverse("sale-list"), payload, format="json")
        item_id = create_response.data["items"][0]["id"]

        item = SaleItem.objects.get(pk=item_id)
        item.quantity = 8  # sell 3 more
        item.save()

        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 42)  # 50 - 8, not 50 - 5 - 8

        item.quantity = 2  # now sell fewer — should restore the difference
        item.save()

        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 48)  # 50 - 2

    def test_editing_sale_item_beyond_available_stock_is_rejected(self):
        self._login_admin()
        payload = {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 5}]}
        create_response = self.client.post(reverse("sale-list"), payload, format="json")
        item_id = create_response.data["items"][0]["id"]

        item = SaleItem.objects.get(pk=item_id)
        item.quantity = 5 + self.chair.quantity_in_stock + 1  # impossible increase
        with self.assertRaises(ValueError):
            item.save()

        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 45)  # unchanged

    def test_search_by_invoice_number(self):
        self._login_admin()
        payload = {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 1}]}
        create_response = self.client.post(reverse("sale-list"), payload, format="json")
        invoice_number = create_response.data["invoice_number"]

        response = self.client.get(reverse("sale-list"), {"search": invoice_number})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["invoice_number"], invoice_number)

    def test_summary_reports_todays_sales_and_revenue(self):
        self._login_admin()
        self.client.post(
            reverse("sale-list"),
            {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 2}]},
            format="json",
        )
        self.client.post(
            reverse("sale-list"),
            {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.table.id, "quantity": 1}]},
            format="json",
        )

        response = self.client.get(reverse("sale-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["todays_sales"], 2)
        self.assertEqual(
            Decimal(response.data["todays_revenue"]),
            Decimal("500.00") * 2 + Decimal("2000.00"),
        )

    def _record_sale(self, quantity=1):
        """Creates an invoice for `quantity` chairs and returns its id."""
        response = self.client.post(
            reverse("sale-list"),
            {
                "sold_to": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": quantity}],
            },
            format="json",
        )
        return response.data["id"]

    def test_admin_can_correct_an_invoice_header(self):
        self._login_admin()
        sale_id = self._record_sale()

        response = self.client.patch(
            reverse("sale-detail", args=[sale_id]),
            {"sold_to": "Shyam Industries Pvt. Ltd."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sold_to"], "Shyam Industries Pvt. Ltd.")

        # Header-only edits must leave the line items and stock alone.
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 49)

    def test_admin_can_rewrite_line_items_and_stock_follows(self):
        self._login_admin()
        sale_id = self._record_sale(quantity=5)
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 45)

        response = self.client.put(
            reverse("sale-detail", args=[sale_id]),
            {
                "sold_to": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("1000.00"))

        # 3 of the 5 chairs come back to stock.
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 48)

    def test_invoice_number_and_date_survive_an_update(self):
        self._login_admin()
        sale_id = self._record_sale()
        original = self.client.get(reverse("sale-detail", args=[sale_id])).data

        response = self.client.patch(
            reverse("sale-detail", args=[sale_id]),
            {"invoice_number": "INV-TAMPERED", "sold_to": "Renamed Ltd."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoice_number"], original["invoice_number"])
        self.assertEqual(response.data["sale_date"], original["sale_date"])

    def test_update_that_outruns_stock_changes_nothing(self):
        self._login_admin()
        sale_id = self._record_sale(quantity=5)

        response = self.client.put(
            reverse("sale-detail", args=[sale_id]),
            {
                "sold_to": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 500}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        sale = Sale.objects.get(pk=sale_id)
        self.assertEqual(sale.total_amount, Decimal("2500.00"))
        self.assertEqual(sale.items.count(), 1)
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 45)

    def test_manager_can_read_sales_but_never_write_them(self):
        """The whole Manager sales rule, enforced at the API not the UI."""
        self._login_admin()
        sale_id = self._record_sale()
        self.client.logout()

        manager = User.objects.create_user(
            username="manager_user",
            password=self.password,
            role=User.Role.INVENTORY_MANAGER,
        )
        self.client.login(username=manager.username, password=self.password)

        self.assertEqual(
            self.client.get(reverse("sale-list")).status_code, status.HTTP_200_OK
        )

        create = self.client.post(
            reverse("sale-list"),
            {
                "sold_to": "Manager Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)

        for method in ("put", "patch"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    reverse("sale-detail", args=[sale_id]),
                    {"sold_to": "Manager Ltd."},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        delete = self.client.delete(reverse("sale-detail", args=[sale_id]))
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Sale.objects.filter(pk=sale_id).exists())

    def test_employee_cannot_even_read_sales(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.get(reverse("sale-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    @override_settings(TIME_ZONE="Asia/Kathmandu")
    def test_today_follows_local_time_not_utc(self):
        """00:30 local time is still the previous day in UTC; it must count as today."""
        self._login_admin()
        sale_id = self._record_sale()
        today = timezone.localdate()
        early_morning = timezone.make_aware(datetime.combine(today, time(0, 30)))
        Sale.objects.filter(pk=sale_id).update(sale_date=early_morning)

        response = self.client.get(reverse("sale-summary"))
        self.assertEqual(response.data["todays_sales"], 1)

        response = self.client.get(reverse("sale-list"), {"date": today.isoformat()})
        self.assertEqual(len(response.data), 1)

        yesterday = (today - timedelta(days=1)).isoformat()
        response = self.client.get(reverse("sale-list"), {"date": yesterday})
        self.assertEqual(len(response.data), 0)

    def test_malformed_date_filter_is_rejected(self):
        self._login_admin()
        response = self.client.get(reverse("sale-list"), {"date": "23-09-2026"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
