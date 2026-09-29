"""توابع کمکی مشترک برای مشاوران."""
import jdatetime
from django.urls import reverse, NoReverseMatch

# ===== ارقام فارسی =====
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(text):
    """تبدیل ارقام انگلیسی به فارسی."""
    return str(text).translate(_PERSIAN_DIGITS)


# ==================================================
# اعلان تغییر برنامه
# ==================================================

def _notify_schedule_change(request, consultant, message):
    """اعلان به منشی/مدیر در مورد تغییر برنامه مشاور."""
    from notifications.services import notify_secretaries_and_managers

    consultant_name = consultant.get_full_name() or consultant.national_code

    # ساخت لینک با reverse — مقاوم در برابر تغییر URL
    try:
        link = reverse(
            "consultant_month_schedule",
            kwargs={"pk": consultant.pk},
        )
    except NoReverseMatch:
        link = ""

    notify_secretaries_and_managers(
        notif_type="schedule_changed",
        title=f"تغییر برنامه {consultant_name}",
        message=message,
        link=link,
        exclude_user=request.user,
    )


# ==================================================
# وضعیت مؤثر برنامه در یک روز خاص
# ==================================================

def _get_effective_schedule(consultant, target_date):
    """
    دریافت وضعیت مؤثر برنامه در یک روز خاص — از override یا الگوی هفتگی.

    خروجی: dict با کلیدهای:
        is_active (bool), start (str|None), end (str|None),
        blocked_hours (list[int]), source ("override"|"weekly"|"none")
    """
    from ...models import ConsultantScheduleOverride, ConsultantWeeklySchedule

    # اولویت ۱: override
    override = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=target_date,
        to_date__gte=target_date,
    ).first()

    if override:
        if override.is_off:
            return {
                "is_active": False,
                "start": None,
                "end": None,
                "blocked_hours": [],
                "source": "override",
            }
        return {
            "is_active": True,
            "start": override.custom_start.strftime("%H:%M") if override.custom_start else None,
            "end": override.custom_end.strftime("%H:%M") if override.custom_end else None,
            "blocked_hours": sorted(override.blocked_hours or []),
            "source": "override",
        }

    # اولویت ۲: الگوی هفتگی
    j = jdatetime.date.fromgregorian(date=target_date)
    weekday = j.weekday()  # 0=شنبه ... 6=جمعه

    weekly = ConsultantWeeklySchedule.objects.filter(
        consultant=consultant,
        weekday=weekday,
        is_active=True,
    ).first()

    if weekly:
        return {
            "is_active": True,
            "start": weekly.start_time.strftime("%H:%M") if weekly.start_time else None,
            "end": weekly.end_time.strftime("%H:%M") if weekly.end_time else None,
            "blocked_hours": sorted(weekly.blocked_hours or []),
            "source": "weekly",
        }

    return {
        "is_active": False,
        "start": None,
        "end": None,
        "blocked_hours": [],
        "source": "none",
    }


# ==================================================
# تولید پیام خوانا از تفاوت دو وضعیت
# ==================================================

def _schedule_diff_message(before, after):
    """
    تولید پیام خوانا از تفاوت دو وضعیت برنامه.
    اگر تغییری نبود، None برمی‌گرداند.
    """
    parts = []

    # ۱. تغییر وضعیت فعال/غیرفعال
    if before["is_active"] != after["is_active"]:
        if after["is_active"]:
            # از تعطیل به فعال
            parts.append(f"فعال شد — {_fa(after['start'])}–{_fa(after['end'])}")
        else:
            # از فعال به تعطیل
            if before["start"] and before["end"]:
                parts.append(
                    f"تعطیل شد (قبلاً {_fa(before['start'])}–{_fa(before['end'])})"
                )
            else:
                parts.append("تعطیل شد")

    # ۲. تغییر ساعت (وقتی هر دو فعال هستن)
    elif after["is_active"]:
        if before["start"] != after["start"] or before["end"] != after["end"]:
            if before["start"] and before["end"]:
                parts.append(
                    f"ساعت {_fa(before['start'])}–{_fa(before['end'])} → "
                    f"{_fa(after['start'])}–{_fa(after['end'])}"
                )
            else:
                parts.append(f"ساعت جدید: {_fa(after['start'])}–{_fa(after['end'])}")

    # ۳. تغییر ساعت‌های غیرفعال (ناهار، نماز و...)
    before_bh = set(before.get("blocked_hours") or [])
    after_bh = set(after.get("blocked_hours") or [])
    if before_bh != after_bh:
        added = sorted(after_bh - before_bh)
        removed = sorted(before_bh - after_bh)
        if added:
            hours_str = "، ".join(_fa(h) for h in added)
            parts.append(f"ساعت غیرفعال اضافه شد: {hours_str}")
        if removed:
            hours_str = "، ".join(_fa(h) for h in removed)
            parts.append(f"ساعت غیرفعال حذف شد: {hours_str}")

    if not parts:
        return None

    return "، ".join(parts)


# ==================================================
# توابع کمکی عمومی
# ==================================================

def _can_manage_levels(user):
    return user.is_authenticated and user.role in ("manager", "secretary")


def _jalali_full(g_date):
    """مثلاً: ۴ مهر ۱۴۰۵"""
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.day} {months[j.month - 1]} {j.year}"


def _jalali_weekday(g_date):
    weekdays = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    j = jdatetime.date.fromgregorian(date=g_date)
    return weekdays[j.weekday()]