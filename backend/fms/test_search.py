from datetime import date
from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import User
from employees.models import Staff
from inventory.models import Product
from orders.models import Order
from sales.models import Sale


class PrefixSearchTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_user", password="x", role=User.Role.ADMIN, email="boss@f.test"
        )
        self.staff_user = User.objects.create_user(
            username="staff_user", password="x", role=User.Role.STAFF
        )
        for index, name in enumerate(["Pen", "Pencil", "Paper", "Bottle", "Chair"]):
            Product.objects.create(
                product_name=name, sku=f"SKU-{index}", selling_price=Decimal("1")
            )
        order = Order.objects.create(order_number="ORD-1001", customer_name="Ram Traders")
        Order.objects.create(
            order_number="ORD-2002", customer_name="Shyam Pvt", status=Order.Status.CANCELLED
        )
        Sale.objects.create(invoice_number="INV-1001", sold_to="Gorkha Steel", order=order)
        Sale.objects.create(invoice_number="INV-2002", sold_to="Ram Bahadur")
        Staff.objects.create(
            full_name="Ram Bahadur Thapa",
            designation="Welder",
            phone="9800000000",
            joining_date=date(2026, 1, 1),
            salary=Decimal("1"),
        )
        self.client.force_authenticate(self.admin)

    def names(self, url, search, key, **params):
        response = self.client.get(url, {"search": search, **params})
        self.assertEqual(response.status_code, 200)
        return sorted(row[key] for row in response.data)

    def test_products_narrow_as_you_type(self):
        products = lambda q: self.names("/api/products/", q, "product_name")
        self.assertEqual(products("p"), ["Paper", "Pen", "Pencil"])
        self.assertEqual(products("PE"), ["Pen", "Pencil"])
        self.assertEqual(products(" pen "), ["Pen", "Pencil"])
        self.assertEqual(products("penc"), ["Pencil"])
        self.assertEqual(products("en"), [])  # prefix only, not "contains"
        self.assertEqual(len(products("")), 5)
        self.assertEqual(products("sku-3"), ["Bottle"])

    def test_sales_by_invoice_customer_or_order(self):
        sales = lambda q: self.names("/api/sales/", q, "invoice_number")
        self.assertEqual(sales("inv-10"), ["INV-1001"])
        self.assertEqual(sales("ram ba"), ["INV-2002"])
        self.assertEqual(sales("ORD-1"), ["INV-1001"])

    def test_orders_keep_other_filters(self):
        orders = lambda q, **p: self.names("/api/orders/", q, "order_number", **p)
        self.assertEqual(orders("ram"), ["ORD-1001"])
        self.assertEqual(orders("canc"), ["ORD-2002"])
        self.assertEqual(orders("ord", status="CANCELLED"), ["ORD-2002"])

    def test_staff_by_name_phone_or_designation(self):
        for query in ("ram bahadur", "9800", "weld"):
            self.assertEqual(
                self.names("/api/staff/", query, "full_name"), ["Ram Bahadur Thapa"]
            )

    def test_users_by_role_or_email(self):
        self.assertEqual(self.names("/api/users/", "staff", "username"), ["staff_user"])
        self.assertEqual(self.names("/api/users/", "boss", "username"), ["admin_user"])

    def test_overlong_query_is_cut_not_rejected(self):
        self.assertEqual(self.names("/api/products/", "p" * 5000, "product_name"), [])

    def test_search_does_not_bypass_permissions(self):
        self.client.force_authenticate(self.staff_user)
        for url in ("/api/staff/", "/api/users/", "/api/sales/", "/api/orders/"):
            response = self.client.get(url, {"search": "r"})
            self.assertEqual(response.status_code, 403, url)
