# Historical models from apps.get_model() carry no field types.
# pyright: reportAttributeAccessIssue=false
from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = [
    ("accounts", "0006_rename_employee_role_to_staff"),
    ("employees", "0004_employee_email_nullable"),
    ("orders", "0001_initial"),
]
AFTER = [
    ("accounts", "0007_manager_role_and_admin_manager_tables"),
    ("employees", "0005_employee_to_staff"),
    ("orders", "0002_order_created_by"),
]


class EmployeeToStaffMigrationTests(TransactionTestCase):
    """Runs the real migrations over data shaped like the old schema."""

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(BEFORE)
        old = executor.loader.project_state(BEFORE).apps

        User = old.get_model("accounts", "User")
        Employee = old.get_model("employees", "Employee")

        def user(username, role, **extra):
            return User.objects.create(username=username, password="hash$" + username,
                                       role=role, **extra)

        self.admin = user("boss", "ADMIN")
        self.manager = user("mgr", "INVENTORY_MANAGER")
        self.staff = user("worker", "STAFF")
        self.staff_without_record = user("newbie", "STAFF", first_name="New", last_name="Bie")
        self.misplaced_manager = user("mgr2", "INVENTORY_MANAGER")

        def employee(name, **extra):
            return Employee.objects.create(
                full_name=name,
                designation="Operator",
                joining_date=date(2022, 1, 1),
                salary=Decimal("25000.00"),
                **extra,
            )

        self.linked = employee("Worker One", user=self.staff, email="w1@x.io",
                               phone="111", address="Road 1")
        self.unlinked = employee("No Login", email="nl@x.io")
        self.wrong_table = employee("Manager In Employee", user=self.misplaced_manager,
                                    phone="999")

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(AFTER)
        self.apps = executor.loader.project_state(AFTER).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_accounts_keep_ids_usernames_and_password_hashes(self):
        User = self.apps.get_model("accounts", "User")
        moved = User.objects.get(pk=self.manager.pk)
        self.assertEqual(moved.username, "mgr")
        self.assertEqual(moved.password, "hash$mgr")
        self.assertEqual(moved.role, "MANAGER")

    def test_each_role_has_its_own_table(self):
        AdminProfile = self.apps.get_model("accounts", "AdminProfile")
        ManagerProfile = self.apps.get_model("accounts", "ManagerProfile")
        self.assertEqual(
            list(AdminProfile.objects.values_list("user_id", flat=True)), [self.admin.pk]
        )
        self.assertEqual(
            set(ManagerProfile.objects.values_list("user_id", flat=True)),
            {self.manager.pk, self.misplaced_manager.pk},
        )

    def test_staff_records_keep_their_ids_and_hr_data(self):
        Staff = self.apps.get_model("employees", "Staff")
        record = Staff.objects.get(pk=self.linked.pk)
        self.assertEqual(record.user_id, self.staff.pk)
        self.assertEqual(
            (record.full_name, record.email, record.phone, record.address, record.salary),
            ("Worker One", "w1@x.io", "111", "Road 1", Decimal("25000.00")),
        )
        self.assertTrue(Staff.objects.filter(pk=self.unlinked.pk, user__isnull=True).exists())

    def test_no_admin_or_manager_is_left_in_staff(self):
        Staff = self.apps.get_model("employees", "Staff")
        self.assertFalse(Staff.objects.exclude(user__isnull=True).exclude(
            user__role="STAFF").exists())
        self.assertFalse(Staff.objects.filter(pk=self.wrong_table.pk).exists())

        User = self.apps.get_model("accounts", "User")
        self.assertEqual(User.objects.get(pk=self.misplaced_manager.pk).phone_number, "999")

    def test_staff_login_without_a_record_gets_one(self):
        Staff = self.apps.get_model("employees", "Staff")
        record = Staff.objects.get(user_id=self.staff_without_record.pk)
        self.assertEqual(record.full_name, "New Bie")
        self.assertEqual(record.designation, "Unassigned")

    def test_existing_orders_have_no_creator(self):
        Order = self.apps.get_model("orders", "Order")
        field = Order._meta.get_field("created_by")
        self.assertTrue(field.null)
