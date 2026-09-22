from rest_framework import serializers

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "username",
            "full_name",
            "email",
            "phone",
            "address",
            "designation",
            "joining_date",
            "salary",
            "status",
        ]
        read_only_fields = ["id", "username"]
