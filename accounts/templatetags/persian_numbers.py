"""فیلترهای نمایش اعداد و مبالغ به فارسی."""
from django import template

register = template.Library()

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ENGLISH_DIGITS = "0123456789"
PERSIAN_SEP = "٬"
_TRANS = str.maketrans(ENGLISH_DIGITS, PERSIAN_DIGITS)


def to_persian_digits(text):
    """تبدیل ارقام انگلیسی به فارسی."""
    return str(text).translate(_TRANS)


def _format_number(n):
    """عدد با جداکنندهٔ فارسی + ارقام فارسی."""
    s = f"{n:,}".replace(",", PERSIAN_SEP)
    return to_persian_digits(s)


@register.filter
def pnum(value):
    """
    نمایش عدد با جداکنندهٔ هزارگان و ارقام فارسی.
    مثال: 1200000 → ۱٬۲۰۰٬۰۰۰
    """
    if value is None or value == "":
        return "—"
    try:
        n = int(float(value))
    except (ValueError, TypeError):
        return value
    return _format_number(n)


@register.filter
def ptoman(value):
    """
    نمایش مبلغ به تومان با ارقام فارسی.
    مثال: 800000 → ۸۰۰٬۰۰۰ تومان
    """
    if value is None or value == "":
        return "—"
    try:
        n = int(float(value))
    except (ValueError, TypeError):
        return value
    if n == 0:
        return "—"
    return _format_number(n) + " تومان"