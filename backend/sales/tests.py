from decimal import Decimal

from django.urls import reverse
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
            role=User.Role.EMPLOYEE,
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

    def test_update_endpoint_not_allowed(self):
        self._login_admin()
        payload = {"sold_to": "Shyam Pvt. Ltd.", "items_input": [{"product": self.chair.id, "quantity": 1}]}
        create_response = self.client.post(reverse("sale-list"), payload, format="json")
        sale_id = create_response.data["id"]

        response = self.client.put(
            reverse("sale-detail", args=[sale_id]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
