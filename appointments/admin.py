from django.contrib import admin
from .models import WeeklySchedule, TimeOff, Appointment


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = ("physician", "get_day_of_week_display", "start_time", "end_time", "slot_duration", "is_active")
    list_filter = ("day_of_week", "is_active", "physician")
    search_fields = ("physician__first_name", "physician__last_name")


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ("physician", "date", "all_day", "start_time", "end_time", "reason")
    list_filter = ("reason", "all_day", "date")
    search_fields = ("physician__first_name", "physician__last_name")
    date_hierarchy = "date"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient", "physician", "date", "start_time",
        "status", "payment_status", "source", "created_by",
    )
    list_filter = ("status", "payment_status", "source", "date", "physician")
    search_fields = ("patient__first_name", "patient__last_name", "patient__national_code", "reason", "transaction_id")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at", "paid_at", "confirmation_sent_at", "reminder_sent_at")
    fieldsets = (
        ("اطلاعات نوبت", {
            "fields": ("patient", "physician", "date", "start_time", "end_time", "status", "source", "reason", "note"),
        }),
        ("پرداخت (اختیاری)", {
            "classes": ("collapse",),
            "fields": ("payment_status", "payment_amount", "payment_method", "transaction_id", "paid_at"),
        }),
        ("پیامک", {
            "classes": ("collapse",),
            "fields": ("confirmation_sent", "confirmation_sent_at", "reminder_sent", "reminder_sent_at", "reminder_response"),
        }),
        ("تبدیل به ویزیت", {
            "fields": ("visit",),
        }),
        ("متادیتا", {
            "classes": ("collapse",),
            "fields": ("created_by", "created_at", "updated_at"),
        }),
    )