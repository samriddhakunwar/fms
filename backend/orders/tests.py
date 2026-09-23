from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import Product
from sales.models import Sale

from .models import Order, OrderItem


class OrderApiTests(APITestCase):
    """
    Role matrix for orders: Admin full CRUD, Manager add/view/delete but never
    update, Employee nothing at all — enforced by the API, not the UI.
    """

    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username="manager_user",
            password=self.password,
            role=User.Role.INVENTORY_MANAGER,
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

    def _login(self, username):
        self.client.login(username=username, password=self.password)

    def _create_order(self, quantity=4, customer="Shyam Pvt. Ltd."):
        order = Order.objects.create(order_number=f"ORD-T{Order.objects.count():04d}",
                                     customer_name=customer)
        OrderItem.objects.create(
            order=order,
            product=self.chair,
            quantity=quantity,
            unit_price=self.chair.selling_price,
        )
        order.recalculate_total()
        return order

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_admin_can_create_order_and_total_is_computed(self):
        self._login("admin_user")
        response = self.client.post(
            reverse("order-list"),
            {
                "customer_name": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 3}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("1500.00"))
        self.assertTrue(response.data["order_number"].startswith("ORD-"))
        self.assertEqual(response.data["status"], Order.Status.PENDING)

    def test_order_does_not_touch_stock(self):
        self._login("admin_user")
        self.client.post(
            reverse("order-list"),
            {
                "customer_name": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 3}],
            },
            format="json",
        )
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 50)

    def test_manager_can_create_order(self):
        self._login("manager_user")
        response = self.client.post(
            reverse("order-list"),
            {
                "customer_name": "Ram Traders",
                "items_input": [{"product": self.chair.id, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_employee_cannot_create_order(self):
        self._login("employee_user")
        response = self.client.post(
            reverse("order-list"),
            {
                "customer_name": "Ram Traders",
                "items_input": [{"product": self.chair.id, "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_requires_at_least_one_item(self):
        self._login("admin_user")
        response = self.client.post(
            reverse("order-list"),
            {"customer_name": "Ram Traders", "items_input": []},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_cannot_list_orders(self):
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def test_manager_can_list_orders(self):
        self._create_order()
        self._login("manager_user")
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_employee_cannot_list_orders(self):
        self._create_order()
        self._login("employee_user")
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Updating — Admin only
    # ------------------------------------------------------------------

    def test_admin_can_update_order(self):
        order = self._create_order()
        self._login("admin_user")
        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {
                "customer_name": "Renamed Ltd.",
                "items_input": [{"product": self.chair.id, "quantity": 6}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.customer_name, "Renamed Ltd.")
        self.assertEqual(order.total_amount, Decimal("3000.00"))
        self.assertEqual(order.items.count(), 1)

    def test_manager_cannot_update_order(self):
        order = self._create_order()
        self._login("manager_user")
        for method in ("put", "patch"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    reverse("order-detail", args=[order.id]),
                    {"customer_name": "Sneaky Ltd."},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.customer_name, "Shyam Pvt. Ltd.")

    def test_fulfilled_order_cannot_be_edited(self):
        order = self._create_order()
        order.status = Order.Status.FULFILLED
        order.save(update_fields=["status"])
        self._login("admin_user")
        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"customer_name": "Too Late Ltd."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Deleting
    # ------------------------------------------------------------------

    def test_admin_can_delete_order(self):
        order = self._create_order()
        self._login("admin_user")
        response = self.client.delete(reverse("order-detail", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=order.pk).exists())

    def test_manager_can_delete_order(self):
        order = self._create_order()
        self._login("manager_user")
        response = self.client.delete(reverse("order-detail", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_employee_cannot_delete_order(self):
        order = self._create_order()
        self._login("employee_user")
        response = self.client.delete(reverse("order-detail", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    def test_fulfilled_order_cannot_be_deleted(self):
        order = self._create_order()
        self._login("admin_user")
        self.client.post(reverse("order-fulfil", args=[order.id]))
        response = self.client.delete(reverse("order-detail", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())

    # ------------------------------------------------------------------
    # Fulfilment — the Order → Sale bridge
    # ------------------------------------------------------------------

    def test_fulfil_creates_sale_and_deducts_stock(self):
        order = self._create_order(quantity=4)
        self._login("admin_user")
        response = self.client.post(reverse("order-fulfil", args=[order.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 46)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.FULFILLED)

        sale = Sale.objects.get(invoice_number=response.data["invoice_number"])
        self.assertEqual(sale.order_id, order.id)
        self.assertEqual(sale.sold_to, order.customer_name)
        self.assertEqual(sale.total_amount, order.total_amount)

    def test_manager_cannot_fulfil_order(self):
        order = self._create_order()
        self._login("manager_user")
        response = self.client.post(reverse("order-fulfil", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Sale.objects.count(), 0)

    def test_fulfil_is_rejected_when_stock_is_short(self):
        order = self._create_order(quantity=999)
        self._login("admin_user")
        response = self.client.post(reverse("order-fulfil", args=[order.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.chair.refresh_from_db()
        self.assertEqual(self.chair.quantity_in_stock, 50)
        self.assertEqual(Sale.objects.count(), 0)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_order_cannot_be_fulfilled_twice(self):
        order = self._create_order()
        self._login("admin_user")
        self.client.post(reverse("order-fulfil", args=[order.id]))
        response = self.client.post(reverse("order-fulfil", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Sale.objects.count(), 1)

    def test_cancelled_order_cannot_be_fulfilled(self):
        order = self._create_order()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        self._login("admin_user")
        response = self.client.post(reverse("order-fulfil", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
