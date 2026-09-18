from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Product


class ProductApiTests(APITestCase):
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
            role=User.Role.EMPLOYEE,
        )

        self.product = Product.objects.create(
            product_name="Chair",
            sku="SKU-CHAIR",
            selling_price=Decimal("500.00"),
            quantity_in_stock=15,
            minimum_stock_level=20,
        )

    def test_anonymous_user_cannot_access_products(self):
        response = self.client.get(reverse("product-list"))
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_employee_cannot_access_products(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_manager_can_list_products(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_low_stock_flag_and_status_computed_by_backend(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.get(reverse("product-detail", args=[self.product.id]))
        self.assertTrue(response.data["is_low_stock"])
        self.assertEqual(response.data["stock_status"], "LOW_STOCK")

    def test_out_of_stock_status(self):
        self.product.quantity_in_stock = 0
        self.product.save()
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("product-detail", args=[self.product.id]))
        self.assertEqual(response.data["stock_status"], "OUT_OF_STOCK")

    def test_admin_can_create_product(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "product_name": "Table",
            "sku": "SKU-TABLE",
            "selling_price": "2000.00",
            "quantity_in_stock": 10,
            "minimum_stock_level": 2,
        }
        response = self.client.post(reverse("product-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_inventory_manager_can_update_product(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.patch(
            reverse("product-detail", args=[self.product.id]),
            {"quantity_in_stock": 100},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 100)

    def test_employee_cannot_update_product(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.patch(
            reverse("product-detail", args=[self.product.id]),
            {"quantity_in_stock": 100},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_product(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.delete(reverse("product-detail", args=[self.product.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_search_by_name_and_sku(self):
        Product.objects.create(
            product_name="Steel Rod",
            sku="SKU-ROD",
            selling_price=Decimal("100.00"),
            quantity_in_stock=50,
            minimum_stock_level=5,
        )
        self.client.login(username="admin_user", password=self.password)

        by_name = self.client.get(reverse("product-list"), {"search": "chair"})
        self.assertEqual(len(by_name.data), 1)
        self.assertEqual(by_name.data[0]["sku"], "SKU-CHAIR")

        by_sku = self.client.get(reverse("product-list"), {"search": "SKU-ROD"})
        self.assertEqual(len(by_sku.data), 1)
        self.assertEqual(by_sku.data[0]["product_name"], "Steel Rod")

    def test_low_stock_query_filter(self):
        Product.objects.create(
            product_name="Steel Rod",
            sku="SKU-ROD",
            selling_price=Decimal("100.00"),
            quantity_in_stock=50,
            minimum_stock_level=5,
        )
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("product-list"), {"low_stock": "true"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["sku"], "SKU-CHAIR")

    def test_summary_counts_low_and_out_of_stock(self):
        Product.objects.create(
            product_name="Out of Stock Item",
            sku="SKU-OOS",
            selling_price=Decimal("50.00"),
            quantity_in_stock=0,
            minimum_stock_level=5,
        )
        Product.objects.create(
            product_name="Well Stocked Item",
            sku="SKU-OK",
            selling_price=Decimal("50.00"),
            quantity_in_stock=100,
            minimum_stock_level=5,
        )
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("product-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_products"], 3)
        self.assertEqual(response.data["low_stock_products"], 2)  # chair + out-of-stock
        self.assertEqual(response.data["out_of_stock_products"], 1)

    def test_negative_selling_price_rejected(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "product_name": "Bad Product",
            "sku": "SKU-BAD",
            "selling_price": "-5.00",
            "quantity_in_stock": 1,
            "minimum_stock_level": 1,
        }
        response = self.client.post(reverse("product-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
