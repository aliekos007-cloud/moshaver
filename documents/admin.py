from django.contrib import admin
from .models import PatientDocument


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ("patient", "document_type", "title", "uploaded_at", "uploaded_by")
    list_filter = ("document_type", "uploaded_at")
    search_fields = ("patient__first_name", "patient__last_name", "patient__file_number", "title")
    readonly_fields = ("uploaded_at",)