from rest_framework import serializers

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "address",
            "designation",
            "joining_date",
            "salary",
            "status",
        ]
        read_only_fields = ["id"]
