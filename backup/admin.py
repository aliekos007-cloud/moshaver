from django.contrib import admin
from .models import BackupRecord


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ("file_name", "status", "size_display", "created_at", "created_by")
    list_filter = ("status", "created_at")
    readonly_fields = ("file_name", "file_size", "created_at", "created_by", "status", "note")