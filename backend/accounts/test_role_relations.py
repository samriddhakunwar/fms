# pyright: reportAttributeAccessIssue=false

"""
The foreign keys that tie each role table (admin / manager / staff) to the
data it works with, and the activity log that records logins and views.
"""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from employees.models import Staff
from inventory.models import Product, StockMovement
from orders.models import Order, OrderItem
from reports.models import SalesReport
from sales.models import Sale, SaleItem

from .models import ActivityLog, ManagerProfile, User

PASSWORD = "TestPass123!"


class RoleTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_user", password=PASSWORD, role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username="manager_user", password=PASSWORD, role=User.Role.MANAGER
        )
        self.other_manager = User.objects.create_user(
            username="other_manager", password=PASSWORD, role=User.Role.MANAGER
        )
        self.staff_user = User.objects.create_user(
            username="staff_user", password=PASSWORD, role=User.Role.STAFF
        )
        self.admin_profile = self.admin.admin_profile
        self.manager_profile = self.manager.manager_profile
        self.product = Product.objects.create(
            product_name="Chair",
            sku="SKU-CHAIR",
            selling_price=Decimal("500.00"),
            quantity_in_stock=50,
            minimum_stock_level=5,
        )

    def login(self, user):
        self.client.logout()
        self.client.login(username=user.username, password=PASSWORD)

    def movements(self, **filters):
        return StockMovement.objects.filter(product=self.product, **filters)

    def post_sale(self, quantity=3):
        return self.client.post(
            reverse("sale-list"),
            {
                "sold_to": "Shyam Pvt. Ltd.",
                "items_input": [{"product": self.product.pk, "quantity": quantity}],
            },
            format="json",
        )


# Admin <-> Manager / Staff ------------------------------------------------
class AccountManagementTests(RoleTestCase):
    def test_admin_creating_a_manager_sets_created_by_admin(self):
        self.login(self.admin)
        response = self.client.post(
            reverse("manager-account-list"),
            {"username": "new_manager", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by_admin_name"], "admin_user")
        profile = ManagerProfile.objects.get(user__username="new_manager")
        self.assertEqual(profile.created_by_admin, self.admin_profile)

    def test_admin_creating_staff_sets_created_by_admin_and_manager(self):
        self.login(self.admin)
        response = self.client.post(
            reverse("staff-list"),
            {
                "full_name": "Ram Thapa",
                "designation": "Operator",
                "joining_date": "2024-01-01",
                "salary": "25000.00",
                "manager": self.manager_profile.pk,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by_admin"], self.admin_profile.pk)
        self.assertEqual(response.data["created_by_admin_name"], "admin_user")
        self.assertEqual(response.data["manager_name"], "manager_user")
        self.assertIsNotNone(response.data["created_at"])
        staff = Staff.objects.get(pk=response.data["id"])
        self.assertEqual(staff.created_by_admin, self.admin_profile)
        self.assertEqual(staff.manager, self.manager_profile)


# Manager <-> Staff --------------------------------------------------------
class ManagerStaffTests(RoleTestCase):
    def staff(self, name, manager):
        return Staff.objects.create(
            full_name=name,
            designation="Operator",
            joining_date=date(2024, 1, 1),
            salary=Decimal("1.00"),
            manager=manager,
        )

    def test_manager_me_lists_only_their_team(self):
        mine = self.staff("Mine", self.manager_profile)
        theirs = self.staff("Theirs", self.other_manager.manager_profile)
        self.staff("Unassigned", None)

        self.login(self.manager)
        response = self.client.get(reverse("staff-list"), {"manager": "me"})
        self.assertEqual([row["id"] for row in response.data], [mine.pk])

        response = self.client.get(
            reverse("staff-list"), {"manager": self.other_manager.manager_profile.pk}
        )
        self.assertEqual([row["id"] for row in response.data], [theirs.pk])

        response = self.client.get(reverse("staff-list"), {"manager": "bogus"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_viewing_staff_is_logged(self):
        member = self.staff("Mine", self.manager_profile)
        self.login(self.manager)
        self.client.get(reverse("staff-list"))
        self.client.get(reverse("staff-detail", args=[member.pk]))

        views = ActivityLog.objects.filter(user=self.manager, action=ActivityLog.Action.VIEW)
        self.assertEqual(
            sorted(views.values_list("target", "object_id"), key=str),
            sorted([("staff", None), ("staff", member.pk)], key=str),
        )
        self.assertTrue(all(entry.role == "MANAGER" for entry in views))

    def test_staff_viewing_own_profile_is_logged(self):
        record = Staff.objects.create(
            full_name="Me",
            designation="Operator",
            joining_date=date(2024, 1, 1),
            salary=Decimal("1.00"),
            user=self.staff_user,
        )
        self.login(self.staff_user)
        response = self.client.get(reverse("staff-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry = ActivityLog.objects.get(user=self.staff_user, action=ActivityLog.Action.VIEW)
        self.assertEqual((entry.target, entry.object_id), ("staff", record.pk))


# Admin / Manager <-> Product + stock_movement -------------------------------
class ProductTests(RoleTestCase):
    def create_product(self, sku):
        return self.client.post(
            reverse("product-list"),
            {
                "product_name": "Table",
                "sku": sku,
                "selling_price": "2000.00",
                "quantity_in_stock": 12,
                "minimum_stock_level": 2,
            },
        )

    def test_create_sets_the_creators_role_column_and_logs_opening_stock(self):
        for user, admin, manager in (
            (self.admin, self.admin_profile, None),
            (self.manager, None, self.manager_profile),
        ):
            self.login(user)
            response = self.create_product(f"SKU-{user.username}")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["created_by_name"], user.username)

            product = Product.objects.get(pk=response.data["id"])
            self.assertEqual(
                (product.created_by_admin, product.created_by_manager), (admin, manager)
            )
            movement = product.stock_movements.get()
            self.assertEqual(movement.movement_type, StockMovement.MovementType.STOCK_IN)
            self.assertEqual((movement.quantity_change, movement.quantity_after), (12, 12))
            self.assertEqual((movement.admin, movement.manager), (admin, manager))

    def test_edit_sets_updated_by_and_logs_an_adjustment(self):
        self.login(self.manager)
        self.client.patch(
            reverse("product-detail", args=[self.product.pk]), {"quantity_in_stock": 42}
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.updated_by_manager, self.manager_profile)
        self.assertIsNone(self.product.updated_by_admin)

        movement = self.movements().get()
        self.assertEqual(movement.movement_type, StockMovement.MovementType.ADJUSTMENT)
        self.assertEqual((movement.quantity_change, movement.quantity_after), (-8, 42))
        self.assertEqual((movement.admin, movement.manager), (None, self.manager_profile))

        # The next editor replaces the previous one, never both set.
        self.login(self.admin)
        self.client.patch(
            reverse("product-detail", args=[self.product.pk]), {"selling_price": "1.00"}
        )
        self.product.refresh_from_db()
        self.assertEqual(
            (self.product.updated_by_admin, self.product.updated_by_manager),
            (self.admin_profile, None),
        )
        self.assertEqual(self.movements().count(), 1)  # price edits move no stock

    def test_adjust_stock_credits_the_admin_or_manager(self):
        url = reverse("product-adjust-stock", args=[self.product.pk])
        self.login(self.admin)
        response = self.client.post(
            url, {"quantity_change": 25, "movement_type": "STOCK_IN", "reason": "Delivery"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product"]["quantity_in_stock"], 75)
        self.login(self.manager)
        self.client.post(url, {"quantity_change": -5, "movement_type": "STOCK_OUT"})

        rows = list(
            self.movements().order_by("id").values_list(
                "movement_type", "quantity_change", "quantity_after", "admin", "manager"
            )
        )
        self.assertEqual(
            rows,
            [
                ("STOCK_IN", 25, 75, self.admin_profile.pk, None),
                ("STOCK_OUT", -5, 70, None, self.manager_profile.pk),
            ],
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.updated_by_manager, self.manager_profile)

    def test_adjust_stock_validation(self):
        self.login(self.admin)
        url = reverse("product-adjust-stock", args=[self.product.pk])
        for payload in (
            {"quantity_change": -51, "movement_type": "STOCK_OUT"},  # below zero
            {"quantity_change": -3, "movement_type": "STOCK_IN"},
            {"quantity_change": 3, "movement_type": "STOCK_OUT"},
            {"quantity_change": 3, "movement_type": "SALE"},  # sales app only
            {"quantity_change": 0},
        ):
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, payload)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 50)
        self.assertFalse(self.movements().exists())

    def test_movement_lists_filter_by_product_and_type(self):
        self.login(self.manager)
        url = reverse("product-adjust-stock", args=[self.product.pk])
        self.client.post(url, {"quantity_change": 10, "movement_type": "STOCK_IN"})
        self.client.post(url, {"quantity_change": -4, "movement_type": "STOCK_OUT"})

        response = self.client.get(reverse("product-movements", args=[self.product.pk]))
        self.assertEqual([row["quantity_change"] for row in response.data], [-4, 10])
        self.assertEqual(response.data[0]["performed_by_name"], "manager_user")

        response = self.client.get(
            reverse("stock-movement-list"),
            {"product": self.product.pk, "movement_type": "stock_out"},
        )
        self.assertEqual([row["quantity_change"] for row in response.data], [-4])

    def test_staff_can_view_stock_but_not_change_it_and_views_are_logged(self):
        self.login(self.staff_user)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("product-detail", args=[self.product.pk])).status_code,
            200,
        )
        forbidden = [
            self.client.post(
                reverse("product-adjust-stock", args=[self.product.pk]), {"quantity_change": 5}
            ),
            self.client.get(reverse("stock-movement-list")),
            self.client.get(reverse("product-movements", args=[self.product.pk])),
        ]
        self.assertEqual({r.status_code for r in forbidden}, {status.HTTP_403_FORBIDDEN})
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 50)

        views = ActivityLog.objects.filter(user=self.staff_user, action=ActivityLog.Action.VIEW)
        self.assertEqual(
            sorted(views.values_list("target", "object_id"), key=str),
            sorted([("product", None), ("product", self.product.pk)], key=str),
        )

    def test_admin_and_manager_views_of_products_are_not_logged(self):
        for user in (self.admin, self.manager):
            self.login(user)
            self.client.get(reverse("product-list"))
        self.assertFalse(ActivityLog.objects.filter(action=ActivityLog.Action.VIEW).exists())


# Admin <-> Sale -----------------------------------------------------------
class SaleTests(RoleTestCase):
    def test_sale_and_its_deletion_log_sale_and_return(self):
        second_admin = User.objects.create_user(
            username="second_admin", password=PASSWORD, role=User.Role.ADMIN
        )
        self.login(self.admin)
        response = self.post_sale(3)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by_admin"], self.admin_profile.pk)
        self.assertEqual(response.data["created_by_name"], "admin_user")
        sale = Sale.objects.get(pk=response.data["id"])
        self.assertEqual(sale.created_by_admin, self.admin_profile)

        sold = self.movements().get()
        self.assertEqual(sold.movement_type, StockMovement.MovementType.SALE)
        self.assertEqual((sold.quantity_change, sold.quantity_after), (-3, 47))
        self.assertEqual((sold.sale, sold.admin, sold.manager), (sale, self.admin_profile, None))

        # Another Admin deletes the invoice; the return is credited to them.
        self.login(second_admin)
        response = self.client.delete(reverse("sale-detail", args=[sale.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        returned = self.movements(movement_type=StockMovement.MovementType.SALE_RETURN).get()
        self.assertEqual((returned.quantity_change, returned.quantity_after), (3, 50))
        self.assertEqual(returned.admin, second_admin.admin_profile)
        self.assertIsNone(returned.sale)
        self.assertIn(sale.invoice_number, returned.reason)
        sold.refresh_from_db()
        self.assertIsNone(sold.sale)  # the SALE row outlives the invoice

    def test_editing_a_sale_sets_updated_by_admin(self):
        self.login(self.admin)
        sale_id = self.post_sale().data["id"]
        second_admin = User.objects.create_user(
            username="second_admin", password=PASSWORD, role=User.Role.ADMIN
        )
        self.login(second_admin)
        response = self.client.patch(
            reverse("sale-detail", args=[sale_id]), {"sold_to": "Himalaya"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sale = Sale.objects.get(pk=sale_id)
        self.assertEqual(sale.created_by_admin, self.admin_profile)
        self.assertEqual(sale.updated_by_admin, second_admin.admin_profile)

    def test_manager_cannot_create_or_edit_a_sale_but_viewing_is_logged(self):
        self.login(self.admin)
        sale_id = self.post_sale().data["id"]

        self.login(self.manager)
        self.assertEqual(self.post_sale().status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(
            reverse("sale-detail", args=[sale_id]), {"sold_to": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Sale.objects.count(), 1)

        self.client.get(reverse("sale-list"))
        self.client.get(reverse("sale-detail", args=[sale_id]))
        views = ActivityLog.objects.filter(user=self.manager, action=ActivityLog.Action.VIEW)
        self.assertEqual(
            sorted(views.values_list("target", "object_id"), key=str),
            sorted([("sale", None), ("sale", sale_id)], key=str),
        )

    def test_stock_rows_outside_a_request_fall_back_to_the_recording_admin(self):
        sale = Sale.objects.create(
            invoice_number="INV-X", sold_to="Walk-in", created_by_admin=self.admin_profile
        )
        SaleItem(
            sale=sale, product=self.product, quantity=2, unit_price=Decimal("500.00")
        ).save()
        sale.delete()
        self.assertEqual(
            list(self.movements().values_list("movement_type", "admin")),
            [("SALE_RETURN", self.admin_profile.pk), ("SALE", self.admin_profile.pk)],
        )

    def test_fulfilling_an_order_sets_the_sales_created_by_admin(self):
        order = Order.objects.create(order_number="ORD-1", customer_name="Shyam Pvt. Ltd.")
        OrderItem.objects.create(
            order=order, product=self.product, quantity=4, unit_price=Decimal("500.00")
        )
        order.recalculate_total()

        self.login(self.admin)
        response = self.client.post(reverse("order-fulfil", args=[order.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sale = Sale.objects.get(order=order)
        self.assertEqual(sale.created_by_admin, self.admin_profile)
        self.assertEqual(self.movements().get().admin, self.admin_profile)


# Admin / Manager <-> customer_order ----------------------------------------
class OrderTests(RoleTestCase):
    def test_order_records_the_admin_or_manager_column(self):
        for user, admin, manager in (
            (self.admin, self.admin_profile, None),
            (self.manager, None, self.manager_profile),
        ):
            self.login(user)
            response = self.client.post(
                reverse("order-list"),
                {
                    "customer_name": "Ram Traders",
                    "items_input": [{"product": self.product.pk, "quantity": 1}],
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["created_by_admin"], admin and admin.pk)
            self.assertEqual(response.data["created_by_manager"], manager and manager.pk)
            self.assertEqual(response.data["created_by_name"], user.username)
            # Fields from before the role columns still come back.
            self.assertEqual(response.data["created_by"], user.pk)
            self.assertEqual(response.data["created_by_username"], user.username)


# Admin / Manager <-> sales_report ------------------------------------------
class SalesReportTests(RoleTestCase):
    def test_report_is_credited_to_the_admin_or_manager(self):
        for user, admin, manager in (
            (self.admin, self.admin_profile, None),
            (self.manager, None, self.manager_profile),
        ):
            self.login(user)
            response = self.client.get(
                reverse("report_sales"), {"start_date": "2026-01-01", "end_date": "2026-01-31"}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            report = SalesReport.objects.get(pk=response.data["report_id"])
            self.assertEqual((report.admin, report.manager), (admin, manager))
            self.assertEqual(response.data["generated_by"], user.username)
            self.assertIsNotNone(response.data["generated_at"])
            self.assertEqual(
                (report.start_date, report.end_date), (date(2026, 1, 1), date(2026, 1, 31))
            )

    def test_rejected_report_is_not_logged(self):
        self.login(self.admin)
        self.client.get(
            reverse("report_sales"), {"start_date": "2026-02-01", "end_date": "2026-01-01"}
        )
        self.assertFalse(SalesReport.objects.exists())

    def test_history_is_admin_and_manager_only(self):
        self.login(self.admin)
        self.client.get(reverse("report_sales"))
        for user in (self.admin, self.manager):
            self.login(user)
            response = self.client.get(reverse("report_sales_history"))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]["generated_by_name"], "admin_user")
            self.assertEqual(response.data[0]["admin"], self.admin_profile.pk)

        self.login(self.staff_user)
        response = self.client.get(reverse("report_sales_history"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# Everyone <-> activity_log ------------------------------------------------
class LoginActivityTests(RoleTestCase):
    def test_login_logout_and_failed_login_are_logged(self):
        for user in (self.admin, self.manager, self.staff_user):
            response = self.client.post(
                reverse("api_auth_login"), {"username": user.username, "password": PASSWORD}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.client.post(reverse("api_auth_logout"))

        self.client.post(
            reverse("api_auth_login"), {"username": "staff_user", "password": "wrong"}
        )
        self.client.post(reverse("api_auth_login"), {"username": "ghost", "password": "x"})

        rows = list(
            ActivityLog.objects.order_by("id").values_list("user__username", "role", "action")
        )
        self.assertEqual(
            rows,
            [
                ("admin_user", "ADMIN", "LOGIN"),
                ("admin_user", "ADMIN", "LOGOUT"),
                ("manager_user", "MANAGER", "LOGIN"),
                ("manager_user", "MANAGER", "LOGOUT"),
                ("staff_user", "STAFF", "LOGIN"),
                ("staff_user", "STAFF", "LOGOUT"),
                ("staff_user", "STAFF", "LOGIN_FAILED"),
                (None, "", "LOGIN_FAILED"),
            ],
        )
        self.assertTrue(all(ActivityLog.objects.values_list("ip_address", flat=True)))

    def test_logout_without_a_session_logs_nothing(self):
        self.client.post(reverse("api_auth_logout"))
        self.assertFalse(ActivityLog.objects.exists())

    def test_a_logging_failure_never_breaks_the_request(self):
        original = ActivityLog.objects.create

        def broken(**kwargs):
            raise IntegrityError("simulated")

        ActivityLog.objects.create = broken
        try:
            with self.assertLogs("accounts.models", level="ERROR"):
                response = self.client.post(
                    reverse("api_auth_login"),
                    {"username": "admin_user", "password": PASSWORD},
                )
        finally:
            ActivityLog.objects.create = original
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# At-most-one check constraints --------------------------------------------
class OneRoleConstraintTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="a", role=User.Role.ADMIN).admin_profile
        self.manager = User.objects.create_user(
            username="m", role=User.Role.MANAGER
        ).manager_profile
        self.product = Product.objects.create(
            product_name="P", sku="P", selling_price=Decimal("1.00")
        )

    def assertRejected(self, create):
        with self.assertRaises(IntegrityError), transaction.atomic():
            create()

    def test_both_admin_and_manager_set_is_rejected(self):
        both = {"admin": self.admin, "manager": self.manager}
        self.assertRejected(
            lambda: Product.objects.create(
                product_name="X", sku="X1", selling_price=1,
                created_by_admin=self.admin, created_by_manager=self.manager,
            )
        )
        self.assertRejected(
            lambda: Product.objects.create(
                product_name="X", sku="X2", selling_price=1,
                updated_by_admin=self.admin, updated_by_manager=self.manager,
            )
        )
        self.assertRejected(
            lambda: Order.objects.create(
                order_number="O1", customer_name="C",
                created_by_admin=self.admin, created_by_manager=self.manager,
            )
        )
        self.assertRejected(
            lambda: StockMovement.objects.create(
                product=self.product, movement_type="ADJUSTMENT",
                quantity_change=1, quantity_after=1, **both,
            )
        )
        self.assertRejected(
            lambda: SalesReport.objects.create(
                start_date=date(2026, 1, 1), end_date=date(2026, 1, 2), **both
            )
        )

    def test_one_or_neither_is_accepted(self):
        Order.objects.create(order_number="O1", customer_name="C", created_by_admin=self.admin)
        Order.objects.create(order_number="O2", customer_name="C", created_by_manager=self.manager)
        Order.objects.create(order_number="O3", customer_name="C")
        SalesReport.objects.create(
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 1), manager=self.manager
        )

    def test_report_dates_must_not_be_backwards(self):
        self.assertRejected(
            lambda: SalesReport.objects.create(
                start_date=date(2026, 1, 2), end_date=date(2026, 1, 1), admin=self.admin
            )
        )

    def test_staff_login_stays_one_to_one(self):
        user = User.objects.create_user(username="s", role=User.Role.STAFF)
        details = dict(designation="Op", joining_date=date(2024, 1, 1), salary=1)
        Staff.objects.create(full_name="One", user=user, **details)
        self.assertRejected(lambda: Staff.objects.create(full_name="Two", user=user, **details))


# customer_order.created_by -> created_by_admin / created_by_manager ----------
BEFORE = [("orders", "0003_order_created_by_admin_manager")]
AFTER = [("orders", "0004_copy_order_created_by_to_role")]


class OrderCreatedByMigrationTests(TransactionTestCase):
    """Runs orders/0004 over orders shaped like the old schema."""

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(BEFORE)
        old = executor.loader.project_state(BEFORE).apps

        OldUser = old.get_model("accounts", "User")
        OldAdmin = old.get_model("accounts", "AdminProfile")
        OldManager = old.get_model("accounts", "ManagerProfile")
        OldOrder = old.get_model("orders", "Order")

        def user(username, role):
            return OldUser.objects.create(username=username, password="x", role=role)

        admin = user("boss", "ADMIN")
        manager = user("mgr", "MANAGER")
        staff = user("worker", "STAFF")
        orphan_manager = user("lost", "MANAGER")  # role row missing
        self.admin_profile = OldAdmin.objects.create(user=admin)
        self.manager_profile = OldManager.objects.create(user=manager)

        for number, creator in (
            ("BY-ADMIN", admin),
            ("BY-MANAGER", manager),
            ("BY-STAFF", staff),
            ("BY-ORPHAN", orphan_manager),
            ("BY-NOBODY", None),
        ):
            OldOrder.objects.create(order_number=number, customer_name="C", created_by=creator)

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(AFTER)
        self.apps = executor.loader.project_state(AFTER).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_created_by_is_mapped_by_role_and_dropped(self):
        Order = self.apps.get_model("orders", "Order")
        mapped = {
            order.order_number: (order.created_by_admin_id, order.created_by_manager_id)
            for order in Order.objects.all()
        }
        self.assertEqual(
            mapped,
            {
                "BY-ADMIN": (self.admin_profile.pk, None),
                "BY-MANAGER": (None, self.manager_profile.pk),
                "BY-STAFF": (None, None),
                "BY-ORPHAN": (None, None),
                "BY-NOBODY": (None, None),
            },
        )
        self.assertNotIn(
            "created_by_id",
            [c.name for c in connection.introspection.get_table_description(
                connection.cursor(), "customer_order"
            )],
        )

    def test_reversing_restores_created_by(self):
        executor = MigrationExecutor(connection)
        executor.migrate(BEFORE)
        Order = executor.loader.project_state(BEFORE).apps.get_model("orders", "Order")
        restored = dict(Order.objects.values_list("order_number", "created_by__username"))
        self.assertEqual(restored["BY-ADMIN"], "boss")
        self.assertEqual(restored["BY-MANAGER"], "mgr")
        self.assertIsNone(restored["BY-STAFF"])
