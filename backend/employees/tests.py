from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Employee


class EmployeeApiTests(APITestCase):
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
        self.employee_user = User.objects.create_user(
            username="employee_user",
            password=self.password,
            role=User.Role.STAFF,
        )

        self.employee = Employee.objects.create(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="555-0100",
            designation="Machine Operator",
            joining_date=date(2022, 1, 1),
            salary=Decimal("30000.00"),
            status=Employee.Status.ACTIVE,
        )

    def test_manager_can_read_but_not_change_employees(self):
        """Managers view staff records; only Admin may write them."""
        self.client.login(username="manager_user", password=self.password)

        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.post(
            reverse("employee-list"),
            {
                "full_name": "Sneaky Hire",
                "designation": "Ghost",
                "joining_date": "2024-01-01",
                "salary": "1.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(
            reverse("employee-detail", args=[self.employee.id]),
            {"salary": "999999.00"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(
            reverse("employee-detail", args=[self.employee.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Employee.objects.count(), 1)

    def test_employees_endpoint_is_closed_to_staff(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(
            reverse("employee-detail", args=[self.employee.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_create_employee(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "full_name": "John Smith",
            "email": "john@example.com",
            "phone": "555-0101",
            "designation": "Quality Inspector",
            "joining_date": "2023-06-01",
            "salary": "32000.00",
            "status": "ACTIVE",
        }
        response = self.client.post(reverse("employee-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 2)

    def test_admin_can_update_employee(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("employee-detail", args=[self.employee.id]),
            {"status": "INACTIVE"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, "INACTIVE")

    def test_admin_can_delete_employee(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.delete(reverse("employee-detail", args=[self.employee.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Employee.objects.count(), 0)

    def test_search_by_name(self):
        Employee.objects.create(
            full_name="Bob Wilson",
            email="bob@example.com",
            designation="Supervisor",
            joining_date=date(2021, 1, 1),
            salary=Decimal("40000.00"),
        )
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("employee-list"), {"search": "jane"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["full_name"], "Jane Doe")

    def test_summary_returns_total_employees(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("employee-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_employees"], 1)

    def test_filter_by_status(self):
        Employee.objects.create(
            full_name="Bob Wilson",
            email="bob@example.com",
            designation="Supervisor",
            joining_date=date(2021, 1, 1),
            salary=Decimal("40000.00"),
            status=Employee.Status.INACTIVE,
        )
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("employee-list"), {"status": "inactive"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["full_name"], "Bob Wilson")

    def test_admin_can_create_employee_with_new_login(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "full_name": "John Smith",
            "email": "john@example.com",
            "phone": "555-0101",
            "designation": "Quality Inspector",
            "joining_date": "2023-06-01",
            "salary": "32000.00",
            "login_username": "john",
            "login_password": "SecurePass123!",
        }
        response = self.client.post(reverse("employee-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "john")
        self.assertNotIn("login_password", response.data)

        user = User.objects.get(username="john")
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertEqual((user.first_name, user.last_name), ("John", "Smith"))
        self.assertEqual(user.email, "john@example.com")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertEqual(Employee.objects.get(full_name="John Smith").user, user)

    def test_new_login_can_have_another_role(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("employee-detail", args=[self.employee.id]),
            {
                "login_username": "jane_mgr",
                "login_password": "SecurePass123!",
                "login_role": "INVENTORY_MANAGER",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.user.username, "jane_mgr")
        self.assertEqual(self.employee.user.role, User.Role.INVENTORY_MANAGER)

    def test_new_login_rejects_taken_username_and_saves_nothing(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "full_name": "John Smith",
            "designation": "Quality Inspector",
            "joining_date": "2023-06-01",
            "salary": "32000.00",
            "login_username": "Employee_User",
            "login_password": "SecurePass123!",
        }
        response = self.client.post(reverse("employee-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("login_username", response.data)
        self.assertEqual(Employee.objects.count(), 1)

    def test_new_login_requires_a_valid_password(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("employee-detail", args=[self.employee.id]),
            {"login_username": "jane", "login_password": "123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("login_password", response.data)
        self.assertFalse(User.objects.filter(username="jane").exists())

    def test_cannot_create_login_for_already_linked_employee(self):
        self.employee.user = self.employee_user
        self.employee.save()
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("employee-detail", args=[self.employee.id]),
            {"login_username": "jane", "login_password": "SecurePass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("login_username", response.data)


    def test_several_employees_can_have_no_email(self):
        self.client.login(username="admin_user", password=self.password)
        for name in ("No Email One", "No Email Two"):
            response = self.client.post(
                reverse("employee-list"),
                {
                    "full_name": name,
                    "email": "",
                    "designation": "Helper",
                    "joining_date": "2024-01-01",
                    "salary": "15000.00",
                },
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIsNone(response.data["email"])
        self.assertEqual(Employee.objects.filter(email__isnull=True).count(), 2)

    def test_new_login_for_employee_without_email(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(
            reverse("employee-list"),
            {
                "full_name": "Ram Thapa",
                "designation": "Helper",
                "joining_date": "2024-01-01",
                "salary": "15000.00",
                "login_username": "ram",
                "login_password": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username="ram").email, "")


class EmployeeSelfProfileTests(APITestCase):
    """
    Staff see their own HR record and nobody else's. The record is resolved
    from the session user, so there is no id to tamper with.
    """

    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.staff_user = User.objects.create_user(
            username="staff_user", password=self.password, role=User.Role.STAFF
        )
        self.other_user = User.objects.create_user(
            username="other_staff", password=self.password, role=User.Role.STAFF
        )

        self.own_record = Employee.objects.create(
            user=self.staff_user,
            full_name="Jane Doe",
            email="jane@example.com",
            designation="Machine Operator",
            joining_date=date(2022, 1, 1),
            salary=Decimal("30000.00"),
        )
        self.colleague_record = Employee.objects.create(
            user=self.other_user,
            full_name="Bob Wilson",
            email="bob@example.com",
            designation="Supervisor",
            joining_date=date(2021, 1, 1),
            salary=Decimal("40000.00"),
        )

    def test_staff_sees_own_record(self):
        self.client.login(username="staff_user", password=self.password)
        response = self.client.get(reverse("employee-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Jane Doe")
        self.assertEqual(response.data["username"], "staff_user")

    def test_staff_cannot_reach_a_colleague_by_id(self):
        self.client.login(username="staff_user", password=self.password)
        response = self.client.get(
            reverse("employee-detail", args=[self.colleague_record.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("employee-me"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unlinked_account_gets_a_helpful_404(self):
        unlinked = User.objects.create_user(
            username="no_record", password=self.password, role=User.Role.STAFF
        )
        self.client.login(username=unlinked.username, password=self.password)
        response = self.client.get(reverse("employee-me"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No employee record", response.data["detail"])
