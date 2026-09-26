"""
سرویس‌های برنامه‌ریزی مشاور.
"""
from datetime import datetime, timedelta

import jdatetime
from django.utils import timezone

from .models import (
    ConsultantWeeklySchedule,
    ConsultantScheduleOverride,
    ConsultantSlotSettings,
)


# ==================================================
# تعطیلات رسمی ایران
# ==================================================

# ==================================================
# تعطیلات رسمی ایران
# ==================================================

# ===== دیکشنری ترجمهٔ تعطیلات =====
HOLIDAY_TRANSLATIONS = {
    # ===== تعطیلات ثابت =====
    "Nowruz": "نوروز",
    "Sizdah Be-dar": "سیزده‌بدر",
    "Weekend": "جمعه",
    "Islamic Republic Day": "روز جمهوری اسلامی",
    "Nature's Day": "روز طبیعت",

    # ===== تعطیلات مذهبی =====
    "Tasua": "تاسوعای حسینی",
    "Ashura": "عاشورای حسینی",
    "Arbaeen": "اربعین حسینی",
    "Demise of Prophet Muhammad and Imam Hassan": "رحلت پیامبر و شهادت امام حسن",
    "Demise of Prophet Muhammad and Martyrdom of Imam Hassan": "رحلت پیامبر و شهادت امام حسن",
    "Martyrdom of Imam Reza": "شهادت امام رضا",
    "Martyrdom of Imam Hassan": "شهادت امام حسن",
    "Martyrdom of Imam Sadeq": "شهادت امام صادق",
    "Birth of Prophet Muhammad and Imam Ja'far al-Sadiq": "میلاد پیامبر و امام صادق",
    "Birth of Ja'far al-Sadiq": "ولادت امام صادق",
    "Martyrdom of Fatima": "شهادت حضرت فاطمه",
    "Birth of Fatima": "ولادت حضرت فاطمه",
    "Birth of Ali": "ولادت امام علی",
    "Martyrdom of Ali": "شهادت امام علی",
    "Birth of Imam Mahdi": "ولادت امام زمان",
    "Muhammad's first revelation": "مبعث پیامبر",
    " Isra and Mi'raj": "معراج پیامبر",
    "Isra and Mi'raj": "معراج پیامبر",
    "Eid al-Fitr": "عید فطر",
    "Eid al-Adha": "عید قربان",
    "Eid al-Ghadir": "عید غدیر",
    "Eid al-Ghadir Khom": "عید غدیر خم",
    "Eid al-Mab'ath": "عید مبعث",
    "Eid al-Fitr (2)": "تعطیل عید فطر",
    "Eid al-Adha (2)": "تعطیل عید قربان",

    # ===== ملی =====
    "death of Ruhollah Khomeini": "رحلت امام خمینی",
    "Death of Khomeini": "رحلت امام خمینی",
    "Nationalization of the Iranian oil industry": "ملی شدن صنعت نفت",
    "Iranian Oil Industry Nationalization": "ملی شدن صنعت نفت",
    "Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Victory of Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Oil Nationalization Day": "ملی شدن صنعت نفت",
    "Anniversary of Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Anniversary of the Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Anniversary of oil nationalization": "ملی شدن صنعت نفت",
}


def _translate_holiday(name):
    """ترجمهٔ نام تعطیلات به فارسی."""
    if not name:
        return name

    name = name.strip()

    # جست‌وجوی دقیق
    if name in HOLIDAY_TRANSLATIONS:
        return HOLIDAY_TRANSLATIONS[name]

    # جست‌وجوی جزئی
    for eng, fa in HOLIDAY_TRANSLATIONS.items():
        if eng.lower() in name.lower() or name.lower() in eng.lower():
            return fa

    # اگه پیدا نشد، خودش رو برگردون
    return name


# ==================================================
# تعطیلات رسمی ایران
# ==================================================

HOLIDAY_TRANSLATIONS = {
    "Nowruz": "نوروز",
    "Sizdah Be-dar": "سیزده‌بدر",
    "Weekend": "جمعه",
    "Islamic Republic Day": "روز جمهوری اسلامی",
    "Nature's Day": "روز طبیعت",
    "Tasua": "تاسوعای حسینی",
    "Ashura": "عاشورای حسینی",
    "Arbaeen": "اربعین حسینی",
    "Demise of Prophet Muhammad and Imam Hassan": "رحلت پیامبر و شهادت امام حسن",
    "Demise of Prophet Muhammad and Martyrdom of Imam Hassan": "رحلت پیامبر و شهادت امام حسن",
    "Martyrdom of Imam Reza": "شهادت امام رضا",
    "Martyrdom of Imam Hassan": "شهادت امام حسن",
    "Martyrdom of Imam Sadeq": "شهادت امام صادق",
    "Birth of Prophet Muhammad and Imam Ja'far al-Sadiq": "میلاد پیامبر و امام صادق",
    "Birth of Ja'far al-Sadiq": "ولادت امام صادق",
    "Martyrdom of Fatima": "شهادت حضرت فاطمه",
    "Birth of Fatima": "ولادت حضرت فاطمه",
    "Birth of Ali": "ولادت امام علی",
    "Martyrdom of Ali": "شهادت امام علی",
    "Birth of Imam Mahdi": "ولادت امام زمان",
    "Muhammad's first revelation": "مبعث پیامبر",
    "Isra and Mi'raj": "معراج پیامبر",
    "Eid al-Fitr": "عید فطر",
    "Eid al-Adha": "عید قربان",
    "Eid al-Ghadir": "عید غدیر",
    "Eid al-Ghadir Khom": "عید غدیر خم",
    "Eid al-Mab'ath": "عید مبعث",
    "death of Ruhollah Khomeini": "رحلت امام خمینی",
    "Death of Khomeini": "رحلت امام خمینی",
    "Nationalization of the Iranian oil industry": "ملی شدن صنعت نفت",
    "Iranian Oil Industry Nationalization": "ملی شدن صنعت نفت",
    "Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Victory of Islamic Revolution": "پیروزی انقلاب اسلامی",
    "Oil Nationalization Day": "ملی شدن صنعت نفت",
    "Anniversary of Islamic Revolution": "پیروزی انقلاب اسلامی",
}


def _translate_holiday(name):
    """ترجمهٔ نام تعطیلات به فارسی."""
    if not name:
        return name

    name = name.strip()

    if name in HOLIDAY_TRANSLATIONS:
        return HOLIDAY_TRANSLATIONS[name]

    for eng, fa in HOLIDAY_TRANSLATIONS.items():
        if eng.lower() in name.lower() or name.lower() in eng.lower():
            return fa

    return name


def is_official_holiday(g_date):
    """برگرداندن نام تعطیلات (فارسی) یا None."""
    try:
        from iranholidays import off_occasion_solar
        j = jdatetime.date.fromgregorian(date=g_date)
        result = off_occasion_solar(j)
        if result:
            return _translate_holiday(result)
        return None
    except Exception:
        return None
    
# ==================================================
# تبدیل تاریخ
# ==================================================

def gregorian_to_jalali_weekday(g_date):
    """0 = شنبه ... 6 = جمعه"""
    return jdatetime.date.fromgregorian(date=g_date).weekday()


# ==================================================
# بازه‌های فعال مشاور در یک تاریخ
# ==================================================

def get_availability(consultant, target_date):
    """بازهٔ فعال مشاور در یک تاریخ. اولویت: Override > Weekly"""
    override = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=target_date,
        to_date__gte=target_date,
    ).first()

    if override:
        if override.is_off:
            return {
                "is_active": False,
                "source": "override",
                "start": None, "end": None,
                "blocked_hours": [],
                "override_id": override.pk,
                "note": override.reason or "مرخصی / تعطیل",
            }

        if override.custom_start and override.custom_end:
            return {
                "is_active": True,
                "source": "override",
                "start": override.custom_start,
                "end": override.custom_end,
                "blocked_hours": list(override.blocked_hours or []),
                "override_id": override.pk,
                "note": override.reason or "ساعت ویژه",
            }

        return {
            "is_active": False,
            "source": "override",
            "start": None, "end": None,
            "blocked_hours": [],
            "override_id": override.pk,
            "note": override.reason or "",
        }

    weekday = gregorian_to_jalali_weekday(target_date)

    weekly = ConsultantWeeklySchedule.objects.filter(
        consultant=consultant,
        weekday=weekday,
        is_active=True,
    ).first()

    if not weekly:
        return {
            "is_active": False,
            "source": "none",
            "start": None, "end": None,
            "blocked_hours": [],
            "override_id": None,
            "note": "بدون برنامه",
        }

    return {
        "is_active": True,
        "source": "weekly",
        "start": weekly.start_time,
        "end": weekly.end_time,
        "blocked_hours": list(weekly.blocked_hours or []),
        "override_id": None,
        "note": "",
    }


# ==================================================
# تنظیمات اسلات
# ==================================================

def get_slot_settings(consultant):
    settings_obj, _ = ConsultantSlotSettings.objects.get_or_create(
        consultant=consultant,
        defaults={
            "slot_minutes": 45,
            "buffer_minutes": 0,
            "max_daily_sessions": 8,
            "allow_overlap": False,
        },
    )
    return settings_obj


# ==================================================
# تولید اسلات‌های یک روز
# ==================================================

def generate_slots(consultant, target_date):
    availability = get_availability(consultant, target_date)

    if not availability["is_active"]:
        return []

    settings_obj = get_slot_settings(consultant)
    slot_minutes = settings_obj.slot_minutes
    buffer_minutes = settings_obj.buffer_minutes
    blocked_hours = set(availability.get("blocked_hours", []))

    slots = []
    current = datetime.combine(target_date, availability["start"])
    end_dt = datetime.combine(target_date, availability["end"])

    while current + timedelta(minutes=slot_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=slot_minutes)

        if current.hour in blocked_hours:
            current = slot_end + timedelta(minutes=buffer_minutes)
            continue

        slots.append({
            "start": current.time(),
            "end": slot_end.time(),
            "start_dt": current,
            "end_dt": slot_end,
            "is_free": True,
            "status": "free",
            "session_id": None,
            "client_name": None,
        })

        current = slot_end + timedelta(minutes=buffer_minutes)

    _mark_slot_statuses(consultant, target_date, slots)
    return slots


def _mark_slot_statuses(consultant, target_date, slots):
    from records.models import Session

    sessions = Session.objects.filter(
        consultant=consultant,
        scheduled_start__date=target_date,
        status__in=["scheduled", "in_progress", "paused"],
    ).select_related("client")

    now = timezone.localtime()
    is_today = (target_date == now.date())

    for slot in slots:
        slot_dt_aware = timezone.make_aware(slot["start_dt"]) if timezone.is_naive(slot["start_dt"]) else slot["start_dt"]

        matched = None
        for s in sessions:
            s_local = timezone.localtime(s.scheduled_start)
            if s_local == slot_dt_aware or (
                s_local >= slot_dt_aware and
                s_local < slot_dt_aware + timedelta(minutes=45)
            ):
                matched = s
                break

        if matched:
            slot["is_free"] = False
            slot["status"] = "booked"
            slot["session_id"] = matched.pk
            slot["client_name"] = matched.client.full_name
            continue

        if is_today and slot_dt_aware < now:
            slot["is_free"] = False
            slot["status"] = "past"


# ==================================================
# نزدیک‌ترین نوبت خالی
# ==================================================

def find_nearest_slot(consultant, max_days=90):
    today = timezone.localdate()

    for i in range(max_days):
        target_date = today + timedelta(days=i)
        slots = generate_slots(consultant, target_date)

        free = [s for s in slots if s["is_free"]]
        if free:
            first = free[0]
            return {
                "found": True,
                "date": target_date,
                "start": first["start"],
                "end": first["end"],
                "days_ahead": i,
            }

    return {"found": False}


# ==================================================
# خلاصهٔ چند روز
# ==================================================

def get_days_summary(consultant, days=30):
    today = timezone.localdate()
    result = {}

    for i in range(days):
        target_date = today + timedelta(days=i)
        slots = generate_slots(consultant, target_date)

        total = len(slots)
        free = len([s for s in slots if s["is_free"]])
        booked = total - free

        if total == 0:
            status = "empty"
        elif free == 0:
            status = "full"
        elif free == total:
            status = "free"
        else:
            status = "partial"

        result[target_date] = {
            "total": total, "free": free, "booked": booked, "status": status,
        }

    return result


# ==================================================
# تقویم ماهانه
# ==================================================

def get_month_schedule(consultant, year, month):
    """
    خلاصهٔ کل ماه جلالی.
    """
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]

    first_j = jdatetime.date(year, month, 1)
    if month == 12:
        next_j = jdatetime.date(year + 1, 1, 1)
    else:
        next_j = jdatetime.date(year, month + 1, 1)

    days_count = (next_j.togregorian() - first_j.togregorian()).days

    today = timezone.localdate()
    today_j = jdatetime.date.fromgregorian(date=today)

    days = []
    for day_num in range(1, days_count + 1):
        try:
            j_date = jdatetime.date(year, month, day_num)
        except ValueError:
            break

        g_date = j_date.togregorian()
        avail = get_availability(consultant, g_date)
        holiday_name = is_official_holiday(g_date)

        is_past = g_date < today
        is_today = g_date == today
        is_friday = j_date.weekday() == 6  # جمعه

        days.append({
            "date": g_date,
            "date_iso": g_date.isoformat(),
            "date_jalali": j_date,
            "day": day_num,
            "weekday": j_date.weekday(),
            "is_past": is_past,
            "is_today": is_today,
            "is_friday": is_friday,
            "is_active": avail["is_active"],
            "start": avail["start"].strftime("%H:%M") if avail["start"] else None,
            "end": avail["end"].strftime("%H:%M") if avail["end"] else None,
            "blocked_hours": avail["blocked_hours"],
            "source": avail["source"],
            "override_id": avail["override_id"],
            "note": avail.get("note", ""),
            "is_holiday": holiday_name is not None,
            "holiday_name": holiday_name,
        })

    return {
        "year": year,
        "month": month,
        "month_name": month_names[month - 1],
        "days": days,
        "first_weekday": first_j.weekday(),
        "days_count": days_count,
        "today": today,
        "today_jalali": today_j,
    }


def get_prev_next_month(year, month):
    """ماه قبل و بعد."""
    if month == 1:
        return (year - 1, 12), (year, 2)
    elif month == 12:
        return (year, 11), (year + 1, 1)
    else:
        return (year, month - 1), (year, month + 1)