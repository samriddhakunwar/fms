from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR

from fms.actor import admin_of

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """Staff (employee) HR records. Admins and Managers are not listed here."""

    list_display = (
        "full_name",
        "user",
        "designation",
        "manager",
        "email",
        "phone",
        "salary",
        "status",
        "joining_date",
    )

    list_select_related = ("user", "manager__user")
    list_display_links = ("full_name",)
    list_editable = ("status",)
    list_filter = ("status", "designation", "manager")
    search_fields = ("full_name", "email", "designation", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = ("created_by_admin", "created_at", "updated_at")
    actions = ("deactivate_staff", "reactivate_staff")
    ordering = ("full_name",)
    date_hierarchy = "joining_date"

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_admin = admin_of(request.user)
        super().save_model(request, obj, form, change)

    @admin.action(description="Deactivate selected staff (soft delete)")
    def deactivate_staff(self, request, queryset):
        updated = queryset.update(status=Staff.Status.INACTIVE)
        self.message_user(
            request,
            f"{updated} staff record(s) marked Inactive. Their record is kept.",
        )

    @admin.action(description="Reactivate selected staff")
    def reactivate_staff(self, request, queryset):
        updated = queryset.update(status=Staff.Status.ACTIVE)
        self.message_user(request, f"{updated} staff record(s) marked Active.")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if IS_POPUP_VAR in request.GET and "status__exact" not in request.GET:
            queryset = queryset.filter(status=Staff.Status.ACTIVE)
        return queryset

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
                    "Link the staff member's login account (Staff role only) so "
                    "they can see their own profile in the app. Optional."
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
                    "manager",
                ),
            },
        ),
        (
            "Record",
            {
                "fields": ("created_by_admin", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
