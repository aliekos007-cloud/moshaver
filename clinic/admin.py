from django.contrib import admin
from .models import ClinicSettings


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ("clinic_name", "doctor_name", "specialty", "phone")