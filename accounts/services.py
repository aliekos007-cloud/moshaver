"""
سرویس‌های برنامه‌ریزی مشاور — محاسبهٔ بازه‌های فعال و تولید اسلات‌های نوبت.
"""
from datetime import datetime, timedelta, date as date_type
from typing import Optional

import jdatetime
from django.utils import timezone

from .models import (
    ConsultantWeeklySchedule,
    ConsultantScheduleOverride,
    ConsultantSlotSettings,
)


# ==================================================
# تبدیل تاریخ جلالی
# ==================================================

def gregorian_to_jalali_weekday(g_date: date_type) -> int:
    """
    تبدیل تاریخ میلادی به روز هفتهٔ جلالی.
    0 = شنبه، 1 = یک‌شنبه، ... 6 = جمعه
    """
    # jdatetime.weekday: 0=شنبه ... 6=جمعه
    j = jdatetime.date.fromgregorian(date=g_date)
    return j.weekday()


# ==================================================
# دریافت بازه‌های فعال مشاور در یک تاریخ
# ==================================================

def get_availability(consultant, target_date: date_type) -> list:
    """
    برگرداندن لیست بازه‌های زمانی فعال مشاور در یک تاریخ مشخص.

    اولویت:
      1) Override (استثنا) — اگه وجود داشت، Weekly نادیده گرفته می‌شود
      2) Weekly Schedule

    خروجی: [{"start": time, "end": time, "source": "override"|"weekly"}, ...]
    """
    # ۱) چک Override
    override = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=target_date,
        to_date__gte=target_date,
    ).first()

    if override:
        if override.is_off:
            return []  # تعطیل کامل

        if override.custom_start and override.custom_end:
            return [{
                "start": override.custom_start,
                "end": override.custom_end,
                "source": "override",
                "override_id": override.id,
            }]

        # اگه is_off=False و ساعت سفارشی نداشت → یعنی فقط علامت‌گذاری شده، برو سراغ Weekly
        return []

    # ۲) برنامهٔ هفتگی
    weekday = gregorian_to_jalali_weekday(target_date)

    weekly = ConsultantWeeklySchedule.objects.filter(
        consultant=consultant,
        weekday=weekday,
        is_active=True,
    ).first()

    if not weekly:
        return []

    return [{
        "start": weekly.start_time,
        "end": weekly.end_time,
        "source": "weekly",
        "weekly_id": weekly.id,
    }]


# ==================================================
# تنظیمات اسلات مشاور
# ==================================================

def get_slot_settings(consultant) -> ConsultantSlotSettings:
    """
    تنظیمات اسلات مشاور — اگه نداشت، پیش‌فرض ۵۰ دقیقه.
    """
    settings_obj, _ = ConsultantSlotSettings.objects.get_or_create(
        consultant=consultant,
        defaults={
            "slot_minutes": 50,
            "buffer_minutes": 0,
            "max_daily_sessions": 8,
            "allow_overlap": False,
        },
    )
    return settings_obj


# ==================================================
# تولید اسلات‌های آزاد یک روز
# ==================================================

def generate_slots(consultant, target_date: date_type) -> list:
    """
    تولید اسلات‌های نوبت آزاد برای یک تاریخ.

    خروجی:
    [
        {
            "start": time(8, 0),
            "end": time(8, 50),
            "start_dt": datetime,
            "end_dt": datetime,
            "is_booked": bool,
            "appointment_id": int | None,
        },
        ...
    ]
    """
    ranges = get_availability(consultant, target_date)
    if not ranges:
        return []

    settings_obj = get_slot_settings(consultant)
    slot_minutes = settings_obj.slot_minutes
    buffer_minutes = settings_obj.buffer_minutes

    slots = []

    for r in ranges:
        current = datetime.combine(target_date, r["start"])
        end_dt = datetime.combine(target_date, r["end"])

        while current + timedelta(minutes=slot_minutes) <= end_dt:
            slot_end = current + timedelta(minutes=slot_minutes)

            slots.append({
                "start": current.time(),
                "end": slot_end.time(),
                "start_dt": current,
                "end_dt": slot_end,
                "is_booked": False,
                "appointment_id": None,
                "source": r["source"],
            })

            current = slot_end + timedelta(minutes=buffer_minutes)

    # علامت‌گذاری اسلات‌های رزرو‌شده
    _mark_booked_slots(consultant, target_date, slots)

    return slots


def _mark_booked_slots(consultant, target_date: date_type, slots: list):
    """علامت‌گذاری اسلات‌هایی که نوبت فعال دارند."""
    from appointments.models import Appointment

    booked = Appointment.objects.filter(
        physician=consultant,
        date=target_date,
        status__in=["scheduled", "confirmed", "arrived", "in_progress"],
    ).values_list("id", "start_time")

    booked_map = {start_time: appt_id for appt_id, start_time in booked}

    for slot in slots:
        if slot["start"] in booked_map:
            slot["is_booked"] = True
            slot["appointment_id"] = booked_map[slot["start"]]


# ==================================================
# اسلات‌های آزاد (بدون رزرو)
# ==================================================

def get_free_slots(consultant, target_date: date_type) -> list:
    """فقط اسلات‌های آزاد"""
    return [s for s in generate_slots(consultant, target_date) if not s["is_booked"]]


# ==================================================
# بازهٔ چند روزه
# ==================================================

def get_availability_range(consultant, from_date: date_type, days: int = 30) -> dict:
    """
    بازه‌های فعال مشاور در چند روز متوالی.
    خروجی: {date: [ranges], ...}
    """
    result = {}
    for i in range(days):
        d = from_date + timedelta(days=i)
        ranges = get_availability(consultant, d)
        if ranges:
            result[d] = ranges
    return result


# ==================================================
# بررسی تداخل نوبت
# ==================================================

def has_conflict(consultant, target_date: date_type, start_time, end_time, exclude_id=None) -> bool:
    """آیا این بازه با نوبت دیگری تداخل دارد؟"""
    from appointments.models import Appointment

    qs = Appointment.objects.filter(
        physician=consultant,
        date=target_date,
        status__in=["scheduled", "confirmed", "arrived", "in_progress"],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


# ==================================================
# چک بازهٔ مجاز رزرو
# ==================================================

def is_within_booking_horizon(target_date: date_type) -> bool:
    """آیا این تاریخ داخل بازهٔ مجاز رزرو است؟"""
    from clinic.models import ClinicSettings

    clinic = ClinicSettings.get()
    horizon = clinic.booking_horizon_months or 6

    today = timezone.localdate()
    if target_date < today:
        return False

    # محاسبهٔ ماه‌های جلوتر
    max_date = today + timedelta(days=horizon * 30)
    return target_date <= max_date