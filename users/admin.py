"""
Register models to Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Account


class AccountInline(admin.TabularInline):
    """Account"""

    model = Account
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin
    """

    model = User
    list_display = ("email", "name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active", "created_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "image", "email_verified")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email", "name")
    ordering = ("email",)
    inlines = [AccountInline]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    Custom Account Admin
    """

    list_display = ("user", "provider", "provider_account_id", "created_at")
    list_filter = ("provider", "created_at")
    search_fields = ("user__email", "provider", "provider_account_id")
