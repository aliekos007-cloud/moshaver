from django.contrib import admin
from .models import License


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = (
        "license_key", "tier", "licensed_to", "status",
        "is_active", "valid_until", "days_remaining",
    )
    list_filter = ("tier", "status", "is_active")
    search_fields = ("license_key", "serial_number", "licensed_to", "licensed_email")
    readonly_fields = (
        "license_key", "serial_number", "installation_id",
        "created_at", "updated_at", "last_check",
    )
    fieldsets = (
        ("کلید و سریال", {
            "fields": ("license_key", "serial_number", "installation_id", "version"),
        }),
        ("مالک", {
            "fields": ("licensed_to", "licensed_email", "licensed_phone"),
        }),
        ("نوع و محدودیت", {
            "fields": ("tier", "max_users", "max_physicians", "max_branches"),
        }),
        ("ماژول‌ها", {
            "fields": (
                "enable_inventory", "enable_finance", "enable_therapies",
                "enable_documents", "enable_consent", "enable_reports",
                "enable_backup", "enable_audit",
            ),
        }),
        ("تاریخ‌ها", {
            "fields": ("activated_at", "valid_from", "valid_until", "last_check"),
        }),
        ("وضعیت", {
            "fields": ("status", "is_active", "notes"),
        }),
    )