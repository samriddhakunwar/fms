# pyright: reportAttributeAccessIssue=false

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from employees.models import Staff

from .models import AdminProfile, ManagerProfile, User


class AuthApiTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username="manager_user",
            password=self.password,
            role=User.Role.MANAGER,
        )
        self.staff = User.objects.create_user(
            username="staff_user",
            password=self.password,
            role=User.Role.STAFF,
        )

    def test_valid_login_returns_user_and_role(self):
        response = self.client.post(
            reverse("api_auth_login"),
            {"username": "admin_user", "password": self.password},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], "ADMIN")
        self.assertEqual(response.data["message"], "Login successful")

    def test_each_role_logs_in_through_the_same_endpoint(self):
        for username, role in (
            ("admin_user", "ADMIN"),
            ("manager_user", "MANAGER"),
            ("staff_user", "STAFF"),
        ):
            response = self.client.post(
                reverse("api_auth_login"),
                {"username": username, "password": self.password},
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, username)
            self.assertEqual(response.data["user"]["role"], role)
            self.client.post(reverse("api_auth_logout"))

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
        self.assertEqual(response.data["role"], "MANAGER")

    def test_logout_clears_session(self):
        self.client.login(username="staff_user", password=self.password)
        self.assertEqual(
            self.client.get(reverse("api_auth_me")).status_code, status.HTTP_200_OK
        )

        logout_response = self.client.post(reverse("api_auth_logout"))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        after_logout = self.client.get(reverse("api_auth_me"))
        self.assertEqual(after_logout.status_code, status.HTTP_401_UNAUTHORIZED)


class RoleTableTests(APITestCase):
    """Each role's record lives in its own table, kept in step with the role."""

    def test_admin_account_gets_an_admin_row_only(self):
        user = User.objects.create_user(username="a", password="x", role=User.Role.ADMIN)
        self.assertTrue(AdminProfile.objects.filter(user=user).exists())
        self.assertFalse(ManagerProfile.objects.filter(user=user).exists())
        self.assertFalse(Staff.objects.filter(user=user).exists())

    def test_manager_account_gets_a_manager_row_only(self):
        user = User.objects.create_user(username="m", password="x", role=User.Role.MANAGER)
        self.assertTrue(ManagerProfile.objects.filter(user=user).exists())
        self.assertFalse(AdminProfile.objects.filter(user=user).exists())
        self.assertFalse(Staff.objects.filter(user=user).exists())

    def test_staff_account_gets_no_admin_or_manager_row(self):
        user = User.objects.create_user(username="s", password="x", role=User.Role.STAFF)
        self.assertFalse(AdminProfile.objects.filter(user=user).exists())
        self.assertFalse(ManagerProfile.objects.filter(user=user).exists())

    def test_superuser_gets_an_admin_row(self):
        user = User.objects.create_superuser(username="root", email="", password="x")
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(AdminProfile.objects.filter(user=user).exists())

    def test_switching_admin_to_manager_moves_the_row(self):
        user = User.objects.create_user(username="a", password="x", role=User.Role.ADMIN)
        user.role = User.Role.MANAGER
        user.save()
        self.assertFalse(AdminProfile.objects.filter(user=user).exists())
        self.assertTrue(ManagerProfile.objects.filter(user=user).exists())

    def test_account_linked_to_staff_record_cannot_leave_staff_role(self):
        user = User.objects.create_user(username="s", password="x", role=User.Role.STAFF)
        Staff.objects.create(
            user=user,
            full_name="S",
            designation="Helper",
            joining_date=date(2024, 1, 1),
            salary=Decimal("1"),
        )
        user.role = User.Role.MANAGER
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_staff_record_rejects_admin_and_manager_accounts(self):
        for role in (User.Role.ADMIN, User.Role.MANAGER):
            user = User.objects.create_user(username=f"u_{role}", password="x", role=role)
            record = Staff(
                user=user,
                full_name="X",
                designation="X",
                joining_date=date(2024, 1, 1),
                salary=Decimal("1"),
            )
            with self.assertRaises(ValidationError):
                record.full_clean()

    def test_deleting_the_account_removes_its_role_row(self):
        user = User.objects.create_user(username="m", password="x", role=User.Role.MANAGER)
        user.delete()
        self.assertEqual(ManagerProfile.objects.count(), 0)


class AccountManagementApiTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username="manager_user", password=self.password, role=User.Role.MANAGER
        )
        self.staff = User.objects.create_user(
            username="staff_user", password=self.password, role=User.Role.STAFF
        )

    def test_admin_creates_admin_account_and_admin_row(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(
            reverse("admin-account-list"),
            {"username": "second_admin", "password": "SecurePass123!", "first_name": "Sec"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "ADMIN")
        self.assertNotIn("password", response.data)

        created = User.objects.get(username="second_admin")
        self.assertEqual(created.role, User.Role.ADMIN)
        self.assertTrue(created.check_password("SecurePass123!"))
        self.assertEqual(response.data["profile_id"], created.admin_profile.pk)
        self.assertFalse(Staff.objects.filter(user=created).exists())

    def test_admin_creates_manager_account_and_manager_row(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(
            reverse("manager-account-list"),
            {
                "username": "new_manager",
                "password": "SecurePass123!",
                "email": "newmanager@example.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="new_manager")
        self.assertEqual(created.role, User.Role.MANAGER)
        self.assertNotEqual(created.password, "SecurePass123!")
        self.assertTrue(ManagerProfile.objects.filter(user=created).exists())
        self.assertFalse(Staff.objects.filter(user=created).exists())

    def test_role_in_payload_cannot_override_the_endpoint(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(
            reverse("manager-account-list"),
            {"username": "sneaky", "password": "SecurePass123!", "role": "ADMIN"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username="sneaky").role, User.Role.MANAGER)

        response = self.client.patch(
            reverse("manager-account-detail", args=[self.manager.id]), {"role": "ADMIN"}
        )
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.role, User.Role.MANAGER)

    def test_lists_contain_only_their_own_role(self):
        self.client.login(username="admin_user", password=self.password)
        admins = self.client.get(reverse("admin-account-list")).data
        managers = self.client.get(reverse("manager-account-list")).data
        self.assertEqual([a["username"] for a in admins], ["admin_user"])
        self.assertEqual([m["username"] for m in managers], ["manager_user"])

    def test_manager_endpoint_cannot_reach_an_admin_by_id(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("manager-account-detail", args=[self.admin.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_update_and_deactivate_manager(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.patch(
            reverse("manager-account-detail", args=[self.manager.id]),
            {"is_active": False, "last_name": "Renamed"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.manager.refresh_from_db()
        self.assertFalse(self.manager.is_active)
        self.assertEqual(self.manager.last_name, "Renamed")

    def test_admin_can_reset_a_manager_password(self):
        self.client.login(username="admin_user", password=self.password)
        self.client.patch(
            reverse("manager-account-detail", args=[self.manager.id]),
            {"password": "BrandNew456!"},
        )
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password("BrandNew456!"))

    def test_admin_can_delete_manager_and_its_row(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.delete(
            reverse("manager-account-detail", args=[self.manager.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.manager.pk).exists())
        self.assertEqual(ManagerProfile.objects.count(), 0)

    def test_weak_password_is_rejected(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(
            reverse("manager-account-list"),
            {"username": "weak_user", "password": "password"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="weak_user").exists())

    def test_password_is_required_on_create(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.post(reverse("admin-account-list"), {"username": "nopw"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="nopw").exists())

    def test_manager_and_staff_cannot_manage_accounts(self):
        for username in ("manager_user", "staff_user"):
            self.client.login(username=username, password=self.password)
            for name in ("admin-account-list", "manager-account-list", "user-list"):
                self.assertEqual(
                    self.client.get(reverse(name)).status_code,
                    status.HTTP_403_FORBIDDEN,
                    (username, name),
                )
            self.assertEqual(
                self.client.post(
                    reverse("manager-account-list"),
                    {"username": "x", "password": "SecurePass123!"},
                ).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(
                    reverse("admin-account-detail", args=[self.admin.id])
                ).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.client.logout()
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_user_overview_is_read_only_and_filterable(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(len(response.data), 3)
        self.assertNotIn("password", response.data[0])

        response = self.client.get(reverse("user-list"), {"role": "staff"})
        self.assertEqual([u["username"] for u in response.data], ["staff_user"])

        response = self.client.post(
            reverse("user-list"),
            {"username": "x", "password": "SecurePass123!", "role": "ADMIN"},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminSelfLockoutTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.admin = User.objects.create_user(
            username="admin_user", password=self.password, role=User.Role.ADMIN
        )
        self.other_admin = User.objects.create_user(
            username="second_admin", password=self.password, role=User.Role.ADMIN
        )
        self.client.login(username="admin_user", password=self.password)

    def test_admin_cannot_delete_own_account(self):
        response = self.client.delete(reverse("admin-account-detail", args=[self.admin.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_admin_cannot_deactivate_own_account(self):
        response = self.client.patch(
            reverse("admin-account-detail", args=[self.admin.id]), {"is_active": False}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_can_still_edit_own_name(self):
        response = self.client.patch(
            reverse("admin-account-detail", args=[self.admin.id]), {"first_name": "Alice"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, "Alice")

    def test_admin_can_delete_another_admin(self):
        response = self.client.delete(
            reverse("admin-account-detail", args=[self.other_admin.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AdminProfile.objects.count(), 1)
