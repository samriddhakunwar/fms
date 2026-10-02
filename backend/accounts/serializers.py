from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "date_joined",
        ]


class RoleAccountSerializer(serializers.ModelSerializer):
    """
    An Admin or Manager account: the login (in `user`) and its role record
    (in `admin` / `manager`) are created and removed together. The role is
    fixed by the endpoint, so it cannot be changed through here.
    """

    role_value: str = ""
    profile_attr: str = ""

    password = serializers.CharField(write_only=True, required=False, min_length=8)
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "profile_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "date_joined",
            "password",
        ]
        read_only_fields = ["id", "profile_id", "role", "date_joined"]

    def get_profile_id(self, obj):
        profile = getattr(obj, self.profile_attr, None)
        return profile.pk if profile else None

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "This field is required."})
        user = User(**validated_data, role=self.role_value)
        user.set_password(password)
        user.save()  # the post_save signal creates the Admin/Manager row
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminAccountSerializer(RoleAccountSerializer):
    role_value = User.Role.ADMIN
    profile_attr = "admin_profile"


class ManagerAccountSerializer(RoleAccountSerializer):
    role_value = User.Role.MANAGER
    profile_attr = "manager_profile"
