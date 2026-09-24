import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def _to_local_naive(value):
    """تبدیل datetime aware به naive محلی (تهران)."""
    if value is None:
        return None
    try:
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            value = timezone.localtime(value)
            value = value.replace(tzinfo=None)
    except Exception:
        pass
    return value


@register.filter
def jalali(value):
    if not value:
        return "—"
    try:
        if hasattr(value, "date") and callable(value.date):
            value = value.date()
        j = jdatetime.date.fromgregorian(date=value)
        return f"{j.year}/{j.month:02d}/{j.day:02d}"
    except Exception as e:
        return f"##ERR-D: {type(e).__name__}: {e}##"


@register.filter
def jalali_datetime(value):
    if not value:
        return "—"
    try:
        v = _to_local_naive(value)
        j = jdatetime.datetime.fromgregorian(datetime=v)
        return f"{j.year}/{j.month:02d}/{j.day:02d} — {j.hour:02d}:{j.minute:02d}"
    except Exception as e:
        return f"##ERR-DT: {type(e).__name__}: {e}##"


@register.filter
def jalali_full(value):
    if not value:
        return "—"
    try:
        if hasattr(value, "date") and callable(value.date):
            value = value.date()
        j = jdatetime.date.fromgregorian(date=value)
        return f"{j.day} {MONTHS_FA[j.month - 1]} {j.year}"
    except Exception as e:
        return f"##ERR-F: {type(e).__name__}: {e}##"


@register.filter
def jalali_short(value):
    if not value:
        return "—"
    try:
        if hasattr(value, "date") and callable(value.date):
            value = value.date()
        j = jdatetime.date.fromgregorian(date=value)
        return f"{j.day} {MONTHS_FA[j.month - 1]}"
    except Exception:
        return "—"


@register.filter
def jalali_time(value):
    if not value:
        return "—"
    try:
        v = _to_local_naive(value)
        j = jdatetime.datetime.fromgregorian(datetime=v)
        return f"{j.hour:02d}:{j.minute:02d}"
    except Exception:
        return "—"