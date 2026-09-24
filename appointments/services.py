"""سرویس محاسبه اسلات‌های خالی و رزرو."""
from datetime import datetime, timedelta, date, time

import jdatetime
from django.db.models import Q

from .models import WeeklySchedule, TimeOff, Appointment


# تبدیل روز هفته‌ی پایتون به مدل ما
# پایتون: Mon=0, Tue=1, ..., Sat=5, Sun=6
# ما:     Sat=0, Sun=1, Mon=2, Tue=3, Wed=4, Thu=5, Fri=6
PYTHON_TO_OUR_WEEKDAY = {
    5: 0,   # Saturday
    6: 1,   # Sunday
    0: 2,   # Monday
    1: 3,   # Tuesday
    2: 4,   # Wednesday
    3: 5,   # Thursday
    4: 6,   # Friday
}


def get_our_weekday(d):
    """تبدیل تاریخ میلادی به روز هفته‌ی ما."""
    return PYTHON_TO_OUR_WEEKDAY[d.weekday()]


def get_available_slots(physician, target_date):
    """
    لیست اسلات‌های خالی برای یک پزشک در یک تاریخ.
    خروجی: [{"start": time, "end": time, "available": bool, ...}]
    """
    if not physician:
        return []

    our_day = get_our_weekday(target_date)

    # برنامه‌های این روز
    schedules = WeeklySchedule.objects.filter(
        physician=physician,
        day_of_week=our_day,
        is_active=True,
    ).order_by("start_time")

    if not schedules.exists():
        return []

    # مرخصی‌های این روز
    time_offs = TimeOff.objects.filter(physician=physician, date=target_date)

    # نوبت‌های موجود این روز
    existing = Appointment.objects.filter(
        physician=physician,
        date=target_date,
        status__in=["scheduled", "confirmed", "arrived", "in_progress"],
    )

    slots = []

    for sch in schedules:
        current = datetime.combine(target_date, sch.start_time)
        end = datetime.combine(target_date, sch.end_time)
        step = timedelta(minutes=sch.slot_duration)

        while current < end:
            slot_start = current.time()
            slot_end = (current + step).time()

            # چک مرخصی
            is_off = False
            for off in time_offs:
                if off.all_day:
                    is_off = True
                    break
                if off.start_time and off.end_time:
                    if off.start_time <= slot_start < off.end_time:
                        is_off = True
                        break

            # چک نوبت موجود
            taken = None
            for apt in existing:
                if apt.start_time < slot_end and apt.end_time > slot_start:
                    taken = apt
                    break

            slots.append({
                "start": slot_start,
                "end": slot_end,
                "available": (not is_off) and (taken is None),
                "appointment_id": taken.id if taken else None,
                "appointment": taken,
                "status": "off" if is_off else ("taken" if taken else "available"),
            })

            current += step

    return slots


def count_available_slots(physician, target_date):
    """تعداد اسلات‌های خالی."""
    if not physician:
        return 0
    return sum(1 for s in get_available_slots(physician, target_date) if s["available"])


def get_week_appointments(physician=None, start_date=None):
    """نوبت‌های یک هفته (شنبه تا جمعه)."""
    if not start_date:
        start_date = date.today()

    our_day = get_our_weekday(start_date)
    saturday = start_date - timedelta(days=our_day)
    end_date = saturday + timedelta(days=6)

    qs = Appointment.objects.filter(
        date__gte=saturday, date__lte=end_date,
    ).select_related("patient", "physician")

    if physician:
        qs = qs.filter(physician=physician)

    days = []
    for i in range(7):
        d = saturday + timedelta(days=i)
        days.append({
            "date": d,
            "jdate": jdatetime.date.fromgregorian(date=d),
            "appointments": list(qs.filter(date=d)),
        })

    return {
        "start_date": saturday,
        "end_date": end_date,
        "days": days,
    }


def create_visit_from_appointment(appointment, user):
    """تبدیل نوبت به ویزیت."""
    from records.models import Visit

    if appointment.visit:
        return appointment.visit

    visit = Visit.objects.create(
        patient=appointment.patient,
        physician=appointment.physician,
        chief_complaint=appointment.reason or "",
    )
    appointment.visit = visit
    appointment.status = "in_progress"
    appointment.save(update_fields=["visit", "status"])
    return visit