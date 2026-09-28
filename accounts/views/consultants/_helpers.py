"""توابع کمکی مشترک برای مشاوران."""
import jdatetime


def _notify_schedule_change(request, action_text, detail=""):
    """اعلان به منشی/مدیر در مورد تغییر برنامه مشاور."""
    from notifications.services import notify_secretaries_and_managers

    consultant_name = request.user.get_full_name() or request.user.national_code
    message = action_text
    if detail:
        message += f" — {detail}"

    notify_secretaries_and_managers(
        notif_type="schedule_changed",
        title=f"تغییر برنامه {consultant_name}",
        message=message,
        link=f"/accounts/consultants/{request.user.pk}/month-schedule/",
        exclude_user=request.user,
    )


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