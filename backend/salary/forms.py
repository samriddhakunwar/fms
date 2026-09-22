"""
salary/forms.py
===============
Admin form for SalaryPayment.

Employees are retired by setting ``status=INACTIVE`` rather than deleted
(their SalaryPayment rows are PROTECTed so payroll history survives). New
payments must therefore only offer active employees — but a payment
recorded before an employee left still has to be editable, so the employee
already stored on the row stays a valid choice for that row.
"""

from django import forms
from django.db.models import Q

from employees.models import Employee

from .models import SalaryPayment


class SalaryPaymentAdminForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get("employee")
        if field is None:
            return

        allowed = Q(status=Employee.Status.ACTIVE)
        current = self.instance.employee_id
        if current:
            # Keep the already-saved employee selectable so editing an old
            # payment does not fail with "Select a valid choice".
            allowed |= Q(pk=current)
        field.queryset = Employee.objects.filter(allowed)
