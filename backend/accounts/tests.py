from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthApiTests(APITestCase):
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

    def test_valid_login_returns_user_and_role(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"username": "admin_user", "password": self.password},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], "ADMIN")
        self.assertEqual(response.data["message"], "Login successful")

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"username": "admin_user", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["message"], "Invalid username or password")

    def test_unknown_username_is_rejected(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"username": "no_such_user", "password": "whatever"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_fields_returns_400(self):
        response = self.client.post(reverse("api_auth_login"), {"username": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_after_login(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.get(reverse("api_auth_me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "INVENTORY_MANAGER")

    def test_logout_clears_session(self):
        self.client.login(username="employee_user", password=self.password)
        self.assertEqual(
            self.client.get(reverse("api_auth_me")).status_code, status.HTTP_200_OK
        )

        logout_response = self.client.post(reverse("api_auth_logout"))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        after_logout = self.client.get(reverse("api_auth_me"))
        self.assertEqual(after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_each_role_only_reaches_its_own_html_dashboard(self):
        self.client.login(username="employee_user", password=self.password)

        own_dashboard = self.client.get(reverse("accounts:employee_dashboard"))
        self.assertEqual(own_dashboard.status_code, status.HTTP_200_OK)

        admin_dashboard = self.client.get(reverse("accounts:admin_dashboard"))
        self.assertEqual(admin_dashboard.status_code, status.HTTP_302_FOUND)

        inventory_dashboard = self.client.get(
            reverse("accounts:inventory_dashboard")
        )
        self.assertEqual(inventory_dashboard.status_code, status.HTTP_302_FOUND)

    def test_unauthenticated_user_redirected_from_dashboards(self):
        response = self.client.get(reverse("accounts:admin_dashboard"))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn(reverse("accounts:login"), response.url)


class UserManagementApiTests(APITestCase):
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

    def test_only_admin_can_list_users(self):
        self.client.login(username="employee_user", password=self.password)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_create_user_with_hashed_password(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "username": "new_manager",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "Manager",
            "email": "newmanager@example.com",
            "role": "INVENTORY_MANAGER",
        }
        response = self.client.post(reverse("user-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = User.objects.get(username="new_manager")
        self.assertNotEqual(created.password, "SecurePass123!")
        self.assertTrue(created.check_password("SecurePass123!"))
        self.assertEqual(created.role, "INVENTORY_MANAGER")

    def test_admin_can_deactivate_user(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("user-detail", args=[self.employee.id]), {"is_active": False}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)

    def test_password_never_returned_in_response(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("user-detail", args=[self.employee.id]))
        self.assertNotIn("password", response.data)
