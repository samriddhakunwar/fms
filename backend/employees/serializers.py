from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.models import User

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    # Optional: create a login account for this employee in the same request,
    # instead of making it on the Users page and linking it afterwards.
    login_username = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=150
    )
    login_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )
    login_role = serializers.ChoiceField(
        choices=User.Role.choices, write_only=True, required=False, default=User.Role.STAFF
    )

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
            "login_username",
            "login_password",
            "login_role",
        ]
        read_only_fields = ["id", "username"]

    def validate_email(self, value):
        # "" and null both mean "no email"; store NULL so the unique index
        # does not treat two employees without an email as duplicates.
        return value or None

    def validate(self, attrs):
        username = attrs.get("login_username", "").strip()
        if not username:
            return attrs

        linked = attrs.get("user", getattr(self.instance, "user", None))
        if linked is not None:
            raise serializers.ValidationError(
                {"login_username": "This employee is already linked to a login account."}
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
        """Pops the login_* fields and, if a username was given, creates the account."""
        username = validated_data.pop("login_username", "")
        password = validated_data.pop("login_password", "")
        role = validated_data.pop("login_role", User.Role.STAFF)
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
            role=role,
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
