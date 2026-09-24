from django.contrib import admin
from .models import (
    ClinicSettings,
    Room,
    ConsultantDailyPresence,
    ConsultantRoomChange,
)


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ("clinic_name", "manager_name", "specialty", "phone")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "capacity", "is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("order", "name")


@admin.register(ConsultantDailyPresence)
class ConsultantDailyPresenceAdmin(admin.ModelAdmin):
    list_display = ("consultant", "date", "room", "status", "arrived_at", "left_at")
    list_filter = ("status", "date", "room")
    search_fields = ("consultant__first_name", "consultant__last_name")
    date_hierarchy = "date"
    autocomplete_fields = ("consultant", "room")


@admin.register(ConsultantRoomChange)
class ConsultantRoomChangeAdmin(admin.ModelAdmin):
    list_display = ("consultant", "date", "from_room", "to_room", "changed_at", "changed_by")
    list_filter = ("date",)
    search_fields = ("consultant__first_name", "consultant__last_name")
    date_hierarchy = "date"