from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("national_code", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff")
    search_fields = ("national_code", "first_name", "last_name")
    ordering = ("national_code",)
    fieldsets = (
        (None, {"fields": ("national_code", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "phone", "role")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("national_code", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )