from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin interface for the Employee model."""

    # List view
    list_display = (
        "full_name",
        "user",
        "designation",
        "email",
        "phone",
        "salary",
        "status",
        "joining_date",
    )

    list_display_links = ("full_name",)

    list_editable = ("status",)

    list_filter = (
        "status",       # Active / Inactive
        "designation",
    )

    search_fields = (
        "full_name",       # Search by employee name
        "email",           # Search by email address
        "designation",     # Search by job title
        "user__username",  # Search by the linked login account
    )

    raw_id_fields = ("user",)

    actions = ("deactivate_employees", "reactivate_employees")

    # Default sort: alphabetical by full name
    ordering = ("full_name",)

    # Date drill-down based on joining date
    date_hierarchy = "joining_date"

    # Deletion policy
    def has_delete_permission(self, request, obj=None):
        return False

    # Actions
    @admin.action(description="Deactivate selected employees (soft delete)")
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(status=Employee.Status.INACTIVE)
        self.message_user(
            request,
            f"{updated} employee(s) marked Inactive. Their record is kept.",
        )

    @admin.action(description="Reactivate selected employees")
    def reactivate_employees(self, request, queryset):
        updated = queryset.update(status=Employee.Status.ACTIVE)
        self.message_user(request, f"{updated} employee(s) marked Active.")

    # Querysets
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "status__exact" not in request.GET:
            queryset = queryset.filter(status=Employee.Status.ACTIVE)
        return queryset

    # Detail (add / change) view
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "address",
                ),
            },
        ),
        (
            "Login Account",
            {
                "fields": ("user",),
                "description": (
                    "Link the employee's login account so they can see their "
                    "own profile in the app. Optional."
                ),
            },
        ),
        (
            "Employment Details",
            {
                "fields": (
                    "designation",
                    "joining_date",
                    "salary",
                    "status",
                ),
            },
        ),
    )
