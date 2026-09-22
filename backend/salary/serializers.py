from django.db.models import Q
from rest_framework import serializers

from employees.models import Employee

from .models import SalaryPayment


class SalaryPaymentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = SalaryPayment
        fields = [
            "id",
            "employee",
            "employee_name",
            "amount",
            "payment_date",
            "payment_method",
            "remarks",
        ]
        read_only_fields = ["id"]

    def __init__(self, *args, **kwargs):
        """
        Only active employees may be chosen for a new payment. When updating an
        existing payment the employee already on it stays selectable, so a
        payment made before someone left is still editable.
        """
        super().__init__(*args, **kwargs)

        allowed = Q(status=Employee.Status.ACTIVE)
        current = getattr(self.instance, "employee_id", None)
        if current:
            allowed |= Q(pk=current)
        self.fields["employee"].queryset = Employee.objects.filter(allowed)
