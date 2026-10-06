from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.models import ManagerProfile, User

from .models import Staff


class StaffSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)
    # Only Staff logins may be linked — Admins and Managers have their own tables.
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.STAFF),
        required=False,
        allow_null=True,
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=ManagerProfile.objects.select_related("user"),
        required=False,
        allow_null=True,
    )
    manager_name = serializers.SerializerMethodField()
    created_by_admin_name = serializers.SerializerMethodField()

    login_username = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=150
    )
    login_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )

    class Meta:
        model = Staff
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
            "manager",
            "manager_name",
            "created_by_admin",
            "created_by_admin_name",
            "created_at",
            "updated_at",
            "login_username",
            "login_password",
        ]
        read_only_fields = [
            "id",
            "username",
            "created_by_admin",
            "created_at",
            "updated_at",
        ]

    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager_id else None

    def get_created_by_admin_name(self, obj):
        return str(obj.created_by_admin) if obj.created_by_admin_id else None

    def validate_user(self, value):
        if value is None:
            return value
        taken = Staff.objects.filter(user=value)
        if self.instance is not None:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise serializers.ValidationError(
                "This login account is already linked to another staff record."
            )
        return value

    def validate_email(self, value):
        return value or None

    def validate(self, attrs):
        username = attrs.get("login_username", "").strip()
        if not username:
            return attrs

        linked = attrs.get("user", getattr(self.instance, "user", None))
        if linked is not None:
            raise serializers.ValidationError(
                {"login_username": "This staff member is already linked to a login account."}
            )
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                {"login_username": "A user with that username already exists."}
            )

        password = attrs.get("login_password", "")
        if not password:
            raise serializers.ValidationError({"login_password": "This field is required."})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"login_password": list(exc.messages)})

        attrs["login_username"] = username
        return attrs

    def _create_login(self, validated_data):
        username = validated_data.pop("login_username", "")
        password = validated_data.pop("login_password", "")
        if not username:
            return

        full_name = validated_data.get("full_name") or getattr(self.instance, "full_name", "")
        first_name, _, last_name = full_name.partition(" ")
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=validated_data.get("email", getattr(self.instance, "email", "")) or "",
            phone_number=validated_data.get("phone", getattr(self.instance, "phone", "")),
            role=User.Role.STAFF,
        )
        user.set_password(password)
        user.save()
        validated_data["user"] = user

    @transaction.atomic
    def create(self, validated_data):
        self._create_login(validated_data)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        self._create_login(validated_data)
        return super().update(instance, validated_data)
