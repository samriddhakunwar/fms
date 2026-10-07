from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import Product

from .models import Order


class ExpectedDeliveryDateTests(APITestCase):
    def setUp(self):
        User.objects.create_user(
            username="admin_user", password="TestPass123!", role=User.Role.ADMIN
        )
        self.client.login(username="admin_user", password="TestPass123!")
        self.chair = Product.objects.create(
            product_name="Chair",
            sku="SKU-CHAIR",
            selling_price=Decimal("500.00"),
            quantity_in_stock=50,
        )
        self.today = timezone.localdate()

    def _create(self, expected):
        return self.client.post(
            reverse("order-list"),
            {
                "customer_name": "Shyam Pvt. Ltd.",
                "expected_delivery_date": expected.isoformat(),
                "items_input": [{"product": self.chair.id, "quantity": 1}],
            },
            format="json",
        )

    def test_new_order_rejects_a_past_date(self):
        response = self._create(self.today - timedelta(days=1))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["expected_delivery_date"],
            ["Expected delivery date cannot be in the past."],
        )

    def test_new_order_accepts_today_and_later(self):
        for expected in (self.today, self.today + timedelta(days=5)):
            response = self._create(expected)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, expected)

    def test_old_order_stays_editable_but_not_before_its_order_date(self):
        order = Order.objects.create(
            order_number="ORD-OLD",
            customer_name="Shyam Pvt. Ltd.",
            order_date=timezone.now() - timedelta(days=30),
            expected_delivery_date=self.today - timedelta(days=20),
        )
        url = reverse("order-detail", args=[order.pk])

        response = self.client.patch(url, {"notes": "Call first"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            url,
            {"expected_delivery_date": (self.today - timedelta(days=40)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["expected_delivery_date"],
            ["Expected delivery date cannot be before the order date."],
        )
