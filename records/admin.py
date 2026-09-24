from django.contrib import admin
from .models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("patient", "physician", "visited_at")
    list_filter = ("physician",)
    search_fields = ("patient__first_name", "patient__last_name", "patient__file_number")