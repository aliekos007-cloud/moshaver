"""
فیلترهای تاریخ شمسی — با پشتیبانی کامل از timezone.
"""
import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

# ===== ارقام فارسی =====
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
EN_TO_FA = str.maketrans("0123456789", FA_DIGITS)


def _to_fa(text):
    """تبدیل ارقام انگلیسی به فارسی."""
    return str(text).translate(EN_TO_FA)


def _to_jalali(value):
    """
    تبدیل مقدار به jdatetime با مدیریت صحیح timezone.
    """
    if value is None or value == "":
        return None

    # اگه datetime با timezone بود → تبدیل به local و حذف tzinfo
    if hasattr(value, "tzinfo") and value.tzinfo is not None:
        try:
            value = timezone.localtime(value).replace(tzinfo=None)
        except Exception:
            value = value.replace(tzinfo=None)

    try:
        return jdatetime.datetime.fromgregorian(datetime=value)
    except (ValueError, TypeError):
        return None


def _to_jalali_date(value):
    """تبدیل date به jdatetime.date."""
    if value is None or value == "":
        return None

    if hasattr(value, "date") and hasattr(value, "hour"):
        # datetime → فقط تاریخ
        j = _to_jalali(value)
        return j.date() if j else None

    try:
        return jdatetime.date.fromgregorian(date=value)
    except (ValueError, TypeError):
        return None


# ==================================================
# فیلترها
# ==================================================

@register.filter
def jalali(value):
    """
    تاریخ کامل شمسی با ارقام فارسی.
    خروجی: ۱۴۰۵/۰۷/۰۳
    """
    j = _to_jalali_date(value)
    if not j:
        return "—"
    return _to_fa(j.strftime("%Y/%m/%d"))


@register.filter
def jalali_datetime(value):
    """
    تاریخ و ساعت شمسی با ارقام فارسی.
    خروجی: ۱۴۰۵/۰۷/۰۳ — ۱۴:۳۰
    """
    j = _to_jalali(value)
    if not j:
        return "—"
    return _to_fa(j.strftime("%Y/%m/%d — %H:%M"))


@register.filter
def jalali_full(value):
    """
    تاریخ کامل با نام ماه.
    خروجی: ۳ مهر ۱۴۰۵
    """
    j = _to_jalali_date(value)
    if not j:
        return "—"

    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    month_name = months[j.month - 1]
    return f"{_to_fa(j.day)} {month_name} {_to_fa(j.year)}"


@register.filter
def jalali_short(value):
    """
    تاریخ کوتاه.
    خروجی: ۳ مهر
    """
    j = _to_jalali_date(value)
    if not j:
        return "—"

    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    return f"{_to_fa(j.day)} {months[j.month - 1]}"


@register.filter
def jalali_time(value):
    """
    ساعت به فرمت ۲۴ ساعته با ارقام فارسی.
    خروجی: ۱۴:۳۰
    """
    if value is None:
        return "—"

    # اگه datetime بود
    if hasattr(value, "tzinfo") and value.tzinfo is not None:
        try:
            value = timezone.localtime(value)
        except Exception:
            pass

    return _to_fa(value.strftime("%H:%M"))


@register.filter
def jalali_weekday(value):
    """
    نام روز هفته.
    خروجی: شنبه
    """
    j = _to_jalali_date(value)
    if not j:
        return "—"

    weekdays = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    return weekdays[j.weekday()]


@register.filter
def fa_num(value):
    """تبدیل هر عدد به ارقام فارسی."""
    if value is None:
        return "—"
    return _to_fa(value)