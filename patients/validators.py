from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_iranian_national_code(value):
    """
    اعتبارسنجی کد ملی ایران طبق الگوریتم رسمی.
    """
    if not value:
        return

    if not str(value).isdigit():
        raise ValidationError("کد ملی باید فقط شامل اعداد باشد.")

    code = str(value).zfill(10)

    if len(code) != 10:
        raise ValidationError("کد ملی باید ۱۰ رقم باشد.")

    if len(set(code)) == 1:
        raise ValidationError("کد ملی واردشده معتبر نیست (ارقام تکراری).")

    check = int(code[9])
    s = sum(int(code[i]) * (10 - i) for i in range(9))
    r = s % 11

    if r < 2:
        valid = (check == r)
    else:
        valid = (check == 11 - r)

    if not valid:
        raise ValidationError("کد ملی واردشده معتبر نیست.")


# اعتبارسنجی شماره موبایل ایران
validate_iranian_mobile = RegexValidator(
    regex=r'^09(1[0-9]|2[0-9]|3[0-9]|9[0-9])\d{7}$',
    message="شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد. مثال: ۰۹۱۲۳۴۵۶۷۸۹"
)