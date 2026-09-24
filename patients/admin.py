from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("file_number", "first_name", "last_name", "national_code", "mobile", "gender")
    search_fields = ("file_number", "national_code", "first_name", "last_name", "mobile")
    list_filter = ("gender", "marital_status", "is_foreign")
    readonly_fields = ("file_number", "created_at", "updated_at")