from rest_framework import serializers

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
