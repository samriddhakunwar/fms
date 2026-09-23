from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from employees.models import Employee

from .models import SalaryPayment


class SalaryPaymentApiTests(APITestCase):
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
        self.employee_record = Employee.objects.create(
            full_name="Jane Doe",
            email="jane@example.com",
            designation="Machine Operator",
            joining_date=date(2022, 1, 1),
            salary=Decimal("30000.00"),
        )
        self.payment = SalaryPayment.objects.create(
            employee=self.employee_record,
            amount=Decimal("30000.00"),
        )

    def test_only_admin_can_view_salary_payments(self):
        self.client.login(username="manager_user", password=self.password)
        response = self.client.get(reverse("salarypayment-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse("salarypayment-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["employee_name"], "Jane Doe")

    def test_admin_can_create_salary_payment(self):
        self.client.login(username="admin_user", password=self.password)
        payload = {
            "employee": self.employee_record.id,
            "amount": "5000.00",
            "remarks": "Bonus",
        }
        response = self.client.post(reverse("salarypayment-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SalaryPayment.objects.count(), 2)

    def test_admin_can_update_and_delete_salary_payment(self):
        self.client.login(username="admin_user", password=self.password)
        update = self.client.patch(
            reverse("salarypayment-detail", args=[self.payment.id]),
            {"remarks": "Corrected"},
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)

        delete = self.client.delete(
            reverse("salarypayment-detail", args=[self.payment.id])
        )
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SalaryPayment.objects.count(), 0)

    def test_filter_by_employee(self):
        other_employee = Employee.objects.create(
            full_name="Bob Wilson",
            email="bob@example.com",
            designation="Supervisor",
            joining_date=date(2021, 1, 1),
            salary=Decimal("40000.00"),
        )
        SalaryPayment.objects.create(
            employee=other_employee,
            amount=Decimal("40000.00"),
        )
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(
            reverse("salarypayment-list"), {"employee": self.employee_record.id}
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["employee_name"], "Jane Doe")
