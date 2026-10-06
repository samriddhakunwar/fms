from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from fms.actor import admin_of

from .models import ActivityLog, AdminProfile, ManagerProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Every login account. Role records live under Admins / Managers / Staff."""

    # List view
    # Columns shown in the changelist table
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "date_joined",
    )

    # Sidebar filters in the changelist
    list_filter = (
        "role",
        "is_active",   # Filter by active / inactive accounts
        "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    # Default sort order in the changelist
    ordering = ("date_joined",)

    # Detail (add / change) view
    fieldsets = (
        *(BaseUserAdmin.fieldsets or ()),
        (
            # Section title shown in the form
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
                "description": (
                    "Saving an Admin or Manager account creates its Admin / "
                    "Manager record automatically. Staff records (HR details) "
                    "are managed under Staff."
                ),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Factory Management — Role & Contact",
            {
                "fields": ("role", "phone_number"),
                "classes": ("wide",),
            },
        ),
    )

    list_editable = ("is_active",)

    readonly_fields = ("date_joined", "last_login")

    date_hierarchy = "date_joined"


class RoleAccountAddForm(forms.ModelForm):
    """Creates the login account and its Admin/Manager record in one step."""

    role_value: str = ""

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        fields: tuple = ()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two password fields didn't match.")
        elif p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        data = self.cleaned_data
        user = User(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone_number=data["phone_number"],
            role=self.role_value,
        )
        user.set_password(data["password1"])
        user.save()  # the post_save signal creates the role record
        self.instance = self._meta.model.objects.get(user=user)
        self.save_m2m = lambda: None
        return self.instance


class AdminAddForm(RoleAccountAddForm):
    role_value = User.Role.ADMIN

    class Meta(RoleAccountAddForm.Meta):
        model = AdminProfile


class ManagerAddForm(RoleAccountAddForm):
    role_value = User.Role.MANAGER

    class Meta(RoleAccountAddForm.Meta):
        model = ManagerProfile


class RoleProfileAdmin(admin.ModelAdmin):
    add_form: type[forms.ModelForm]

    list_display = ("username", "full_name", "email", "phone", "is_active", "created_at")
    list_select_related = ("user",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    list_filter = ("user__is_active",)
    ordering = ("user__username",)
    readonly_fields = ("user", "created_at")
    fields = ("user", "created_at")

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is None:
            kwargs["form"] = self.add_form
            kwargs["fields"] = None
        return super().get_form(request, obj, change=change, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (
                    "Login Account",
                    {"fields": ("username", "password1", "password2")},
                ),
                (
                    "Contact",
                    {"fields": ("first_name", "last_name", "email", "phone_number")},
                ),
            )
        return (
            (
                None,
                {
                    "fields": self.readonly_fields,
                    "description": (
                        "Edit the name, email, password or active status on the "
                        "linked login account."
                    ),
                },
            ),
        )

    def get_readonly_fields(self, request, obj=None):
        return () if obj is None else self.readonly_fields

    @admin.display(description="Username", ordering="user__username")
    def username(self, obj):
        return obj.user.username

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(description="Email")
    def email(self, obj):
        return obj.user.email

    @admin.display(description="Phone")
    def phone(self, obj):
        return obj.user.phone_number

    @admin.display(description="Active", boolean=True)
    def is_active(self, obj):
        return obj.user.is_active

    # Deleting a role record deletes the account behind it, so no login is
    # left with a role but no record.
    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        if queryset.filter(user=request.user).exists():
            self.message_user(
                request, "You cannot delete your own account.", messages.ERROR
            )
            queryset = queryset.exclude(user=request.user)
        User.objects.filter(pk__in=queryset.values("user_id")).delete()

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.user_id == request.user.pk:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(AdminProfile)
class AdminProfileAdmin(RoleProfileAdmin):
    add_form = AdminAddForm


@admin.register(ManagerProfile)
class ManagerProfileAdmin(RoleProfileAdmin):
    add_form = ManagerAddForm

    list_display = RoleProfileAdmin.list_display + ("created_by_admin",)
    list_select_related = ("user", "created_by_admin__user")
    readonly_fields = ("user", "created_by_admin", "created_at")
    fields = readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_admin = admin_of(request.user)
        super().save_model(request, obj, form, change)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Logins, logouts and read-only views; written by the API, never edited."""

    list_display = ("created_at", "user", "role", "action", "target", "object_id", "ip_address")
    list_select_related = ("user",)
    list_filter = ("action", "role", "target", "created_at")
    search_fields = ("user__username", "target", "ip_address")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
