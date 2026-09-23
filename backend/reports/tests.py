from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import Product
from sales.models import Sale, SaleItem


class SalesReportTests(APITestCase):
    """
    The sales report: Admin and Manager can generate it, Staff cannot, and the
    figures it returns are the ones the page displays.
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
            quantity_in_stock=500,
            minimum_stock_level=10,
        )
        self.table = Product.objects.create(
            product_name="Table",
            sku="SKU-TABLE",
            selling_price=Decimal("2000.00"),
            quantity_in_stock=500,
            minimum_stock_level=2,
        )

        self.today = timezone.localdate()
        # Two invoices today, one the day before yesterday — so the series has
        # a zero day in the middle and the extremes have something to pick.
        self._sale(self.today, [(self.chair, 2)])
        self._sale(self.today, [(self.table, 1)])
        self._sale(self.today - timedelta(days=2), [(self.chair, 1)])

    def _sale(self, day, lines):
        when = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time().replace(hour=12))
        )
        sale = Sale.objects.create(
            invoice_number=f"INV-T{Sale.objects.count():04d}",
            sold_to="Shyam Pvt. Ltd.",
            sale_date=when,
        )
        total = Decimal("0")
        for product, quantity in lines:
            item = SaleItem(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=product.selling_price,
            )
            item.save()
            total += item.subtotal
        sale.total_amount = total
        sale.save(update_fields=["total_amount"])
        return sale

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def test_admin_can_generate_the_report(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("report_sales"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_can_generate_the_report(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.get(reverse("report_sales"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_generate_the_report(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.get(reverse("report_sales"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_generate_the_report(self):
        response = self.client.get(reverse("report_sales"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def test_default_window_is_the_last_seven_days(self):
        self.client.login(username="admin_user", password=self.password)
        data = self.client.get(reverse("report_sales")).data

        self.assertEqual(len(data["days_series"]), 7)
        self.assertEqual(data["end_date"], self.today.isoformat())
        self.assertEqual(data["totals"]["sales_count"], 3)
        self.assertEqual(
            Decimal(data["totals"]["revenue"]), Decimal("1000.00") + Decimal("2000.00") + Decimal("500.00")
        )
        self.assertEqual(data["totals"]["items_sold"], 4)

    def test_report_breaks_revenue_down_by_product(self):
        self.client.login(username="admin_user", password=self.password)
        products = self.client.get(reverse("report_sales")).data["products"]

        by_sku = {entry["sku"]: entry for entry in products}
        self.assertEqual(by_sku["SKU-CHAIR"]["quantity"], 3)
        self.assertEqual(Decimal(by_sku["SKU-CHAIR"]["revenue"]), Decimal("1500.00"))
        self.assertEqual(by_sku["SKU-TABLE"]["quantity"], 1)
        # Ordered by quantity sold, highest first.
        self.assertEqual(products[0]["sku"], "SKU-CHAIR")

    def test_extremes_ignore_days_without_sales(self):
        self.client.login(username="admin_user", password=self.password)
        data = self.client.get(reverse("report_sales")).data

        self.assertEqual(data["busiest_day"]["day"], self.today.isoformat())
        self.assertEqual(data["busiest_day"]["count"], 2)
        # The quiet day is the one that had a single sale, not one of the
        # empty days in between.
        self.assertEqual(
            data["quietest_day"]["day"], (self.today - timedelta(days=2)).isoformat()
        )
        self.assertEqual(data["quietest_day"]["count"], 1)
        self.assertEqual(data["best_revenue_day"]["day"], self.today.isoformat())
        self.assertEqual(data["totals"]["selling_days"], 2)

    def test_series_is_dense_so_quiet_days_report_zero(self):
        self.client.login(username="admin_user", password=self.password)
        series = self.client.get(reverse("report_sales")).data["days_series"]

        yesterday = (self.today - timedelta(days=1)).isoformat()
        quiet = next(day for day in series if day["day"] == yesterday)
        self.assertEqual(quiet["count"], 0)
        self.assertEqual(Decimal(quiet["revenue"]), Decimal("0"))

    def test_date_range_filters_the_report(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(
            reverse("report_sales"),
            {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()},
        )
        data = response.data

        self.assertEqual(len(data["days_series"]), 1)
        self.assertEqual(data["totals"]["sales_count"], 2)
        self.assertEqual(Decimal(data["totals"]["revenue"]), Decimal("3000.00"))

    def test_empty_range_reports_zeros_rather_than_failing(self):
        self.client.login(username="admin_user", password=self.password)
        far_off = (self.today - timedelta(days=90)).isoformat()
        data = self.client.get(
            reverse("report_sales"), {"start_date": far_off, "end_date": far_off}
        ).data

        self.assertEqual(data["totals"]["sales_count"], 0)
        self.assertEqual(Decimal(data["totals"]["revenue"]), Decimal("0"))
        self.assertIsNone(data["busiest_day"])
        self.assertEqual(data["products"], [])

    def test_backwards_range_is_rejected(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(
            reverse("report_sales"),
            {
                "start_date": self.today.isoformat(),
                "end_date": (self.today - timedelta(days=5)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_date_is_rejected(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("report_sales"), {"start_date": "last-tuesday"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversized_range_is_clamped_and_says_so(self):
        self.client.login(username="admin_user", password=self.password)
        data = self.client.get(
            reverse("report_sales"),
            {
                "start_date": (self.today - timedelta(days=400)).isoformat(),
                "end_date": self.today.isoformat(),
            },
        ).data

        self.assertTrue(data["truncated"])
        self.assertEqual(len(data["days_series"]), 180)
