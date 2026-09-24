from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Role, ConsultantLevel


# ==================================================
# پیام‌های خطای فارسی مشترک
# ==================================================

REQUIRED_MSG = "پر کردن این فیلد الزامی است."
INVALID_MSG = "مقدار وارد شده معتبر نیست."
UNIQUE_MSG = "این مقدار قبلاً ثبت شده است."
MIN_LENGTH_MSG = "این مقدار باید حداقل {n} کاراکتر باشد."


# ==================================================
# فرم‌های کاربر
# ==================================================

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
        }),
        min_length=8,
        error_messages={
            "required": "وارد کردن رمز عبور الزامی است.",
            "min_length": "رمز عبور باید حداقل ۸ کاراکتر باشد.",
        },
        help_text="حداقل ۸ کاراکتر شامل حرف و عدد",
    )
    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
        }),
        error_messages={
            "required": "تکرار رمز عبور الزامی است.",
        },
    )

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "national_code", "phone",
            "role", "consultant_level", "is_active",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "national_code": forms.TextInput(attrs={"class": "form-control", "maxlength": 10}),
            "phone": forms.TextInput(attrs={"class": "form-control", "maxlength": 15}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "consultant_level": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "national_code": "کد ملی",
            "phone": "تلفن همراه",
            "role": "نقش",
            "consultant_level": "سطح مشاور",
            "is_active": "فعال",
        }
        error_messages = {
            "first_name": {"required": "وارد کردن نام الزامی است."},
            "last_name": {"required": "وارد کردن نام خانوادگی الزامی است."},
            "national_code": {
                "required": "وارد کردن کد ملی الزامی است.",
                "unique": "این کد ملی قبلاً ثبت شده است.",
            },
            "role": {"required": "انتخاب نقش الزامی است."},
        }

    def clean_first_name(self):
        name = self.cleaned_data.get("first_name", "").strip()
        if len(name) < 2:
            raise forms.ValidationError("نام باید حداقل ۲ کاراکتر باشد.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get("last_name", "").strip()
        if len(name) < 2:
            raise forms.ValidationError("نام خانوادگی باید حداقل ۲ کاراکتر باشد.")
        return name

    def clean_national_code(self):
        code = self.cleaned_data.get("national_code", "").strip()

        # تبدیل ارقام فارسی به انگلیسی
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        for i, d in enumerate(persian_digits):
            code = code.replace(d, str(i))

        if not code:
            raise forms.ValidationError("وارد کردن کد ملی الزامی است.")
        if not code.isdigit():
            raise forms.ValidationError("کد ملی باید فقط شامل اعداد باشد.")
        if len(code) != 10:
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        if User.objects.filter(national_code=code).exists():
            raise forms.ValidationError("این کد ملی قبلاً برای کاربر دیگری ثبت شده است.")
        return code

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        # تبدیل ارقام فارسی
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        for i, d in enumerate(persian_digits):
            phone = phone.replace(d, str(i))

        if phone and not phone.isdigit():
            raise forms.ValidationError("شماره تلفن باید فقط شامل اعداد باشد.")
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")

        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", "رمز عبور و تکرار آن یکسان نیستند.")

        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                # ترجمهٔ پیام‌های Django به فارسی
                messages_map = {
                    "This password is too short. It must contain at least 8 characters.":
                        "رمز عبور باید حداقل ۸ کاراکتر باشد.",
                    "This password is too common.":
                        "این رمز عبور خیلی رایجه. یه رمز قوی‌تر انتخاب کنید.",
                    "This password is entirely numeric.":
                        "رمز عبور نمی‌تواند فقط شامل اعداد باشد.",
                }
                for msg in e.messages:
                    translated = messages_map.get(msg, msg)
                    self.add_error("password", translated)

        role = cleaned.get("role")
        level = cleaned.get("consultant_level")
        if role == Role.CONSULTANT and not level:
            self.add_error("consultant_level", "برای نقش مشاور، انتخاب سطح الزامی است.")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "national_code", "phone",
            "role", "consultant_level", "is_active",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "national_code": forms.TextInput(attrs={"class": "form-control", "maxlength": 10}),
            "phone": forms.TextInput(attrs={"class": "form-control", "maxlength": 15}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "consultant_level": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "national_code": "کد ملی",
            "phone": "تلفن همراه",
            "role": "نقش",
            "consultant_level": "سطح مشاور",
            "is_active": "فعال",
        }
        error_messages = {
            "first_name": {"required": "وارد کردن نام الزامی است."},
            "last_name": {"required": "وارد کردن نام خانوادگی الزامی است."},
            "national_code": {"required": "وارد کردن کد ملی الزامی است."},
        }

    def clean_national_code(self):
        code = self.cleaned_data.get("national_code", "").strip()
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        for i, d in enumerate(persian_digits):
            code = code.replace(d, str(i))

        if not code:
            raise forms.ValidationError("وارد کردن کد ملی الزامی است.")
        if not code.isdigit():
            raise forms.ValidationError("کد ملی باید فقط شامل اعداد باشد.")
        if len(code) != 10:
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        if User.objects.filter(national_code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("این کد ملی قبلاً برای کاربر دیگری ثبت شده است.")
        return code

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        level = cleaned.get("consultant_level")
        if role == Role.CONSULTANT and not level:
            self.add_error("consultant_level", "برای نقش مشاور، انتخاب سطح الزامی است.")
        return cleaned


class UserPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=8,
        error_messages={
            "required": "وارد کردن رمز عبور جدید الزامی است.",
            "min_length": "رمز عبور باید حداقل ۸ کاراکتر باشد.",
        },
    )
    new_password_confirm = forms.CharField(
        label="تکرار رمز جدید",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={
            "required": "تکرار رمز جدید الزامی است.",
        },
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("new_password_confirm")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password_confirm", "رمز عبور و تکرار آن یکسان نیستند.")

        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                messages_map = {
                    "This password is too short. It must contain at least 8 characters.":
                        "رمز عبور باید حداقل ۸ کاراکتر باشد.",
                    "This password is too common.":
                        "این رمز عبور خیلی رایجه. یه رمز قوی‌تر انتخاب کنید.",
                    "This password is entirely numeric.":
                        "رمز عبور نمی‌تواند فقط شامل اعداد باشد.",
                }
                for msg in e.messages:
                    translated = messages_map.get(msg, msg)
                    self.add_error("new_password", translated)

        return cleaned


# ==================================================
# ویجت اختصاصی برای ورودی عدد فارسی
# ==================================================

class PersianNumberInput(forms.TextInput):
    input_type = "text"

    def __init__(self, attrs=None):
        default_attrs = {
            "class": "form-control persian-number",
            "inputmode": "numeric",
            "autocomplete": "off",
            "dir": "ltr",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


# ==================================================
# فرم سطح مشاور (ConsultantLevel)
# ==================================================

class ConsultantLevelForm(forms.ModelForm):
    class Meta:
        model = ConsultantLevel
        fields = [
            "name",
            "standard_minutes",
            "base_price",
            "overtime_per_minute",
            "grace_minutes",
            "rounding_minutes",
            "max_minutes",
            "insurance_share",
            "effective_from",
            "effective_to",
            "color",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "مثلاً: دکتری، کارشناسی ارشد، کارشناس",
            }),
            "standard_minutes": PersianNumberInput(),
            "base_price": PersianNumberInput(attrs={"placeholder": "مثلاً: 800000"}),
            "overtime_per_minute": PersianNumberInput(attrs={"placeholder": "مثلاً: 20000"}),
            "grace_minutes": PersianNumberInput(),
            "rounding_minutes": PersianNumberInput(),
            "max_minutes": PersianNumberInput(),
            "insurance_share": PersianNumberInput(),
            "effective_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "effective_to": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "color": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "عنوان سطح",
            "standard_minutes": "زمان استاندارد (دقیقه)",
            "base_price": "مبلغ پایه (تومان)",
            "overtime_per_minute": "هزینهٔ هر دقیقهٔ مازاد (تومان)",
            "grace_minutes": "ارفاق (دقیقه)",
            "rounding_minutes": "رُند کردن (دقیقه)",
            "max_minutes": "حداکثر زمان مجاز (دقیقه)",
            "insurance_share": "سهم بیمه (تومان)",
            "effective_from": "از تاریخ",
            "effective_to": "تا تاریخ",
            "color": "رنگ در تایم‌لاین",
            "is_active": "فعال",
        }
        help_texts = {
            "standard_minutes": "مثلاً ۴۵ دقیقه — تا این زمان، مبلغ پایه حساب می‌شود",
            "grace_minutes": "دقایقی که بعد از استاندارد رایگان‌اند (مثلاً ۵ دقیقه)",
            "rounding_minutes": "مازاد بر این عدد رُند می‌شود. ۰ = دقیقه‌ای",
            "max_minutes": "بیش از این زمان، سیستم هشدار می‌دهد",
            "insurance_share": "اگر بیمه قبول نمی‌کنید، ۰ بگذارید",
            "effective_to": "خالی بگذارید اگر هنوز معتبر است",
        }
        error_messages = {
            "name": {"required": "وارد کردن عنوان سطح الزامی است."},
            "standard_minutes": {"required": "زمان استاندارد الزامی است."},
            "base_price": {"required": "مبلغ پایه الزامی است."},
            "overtime_per_minute": {"required": "هزینهٔ هر دقیقهٔ مازاد الزامی است."},
            "effective_from": {"required": "تاریخ شروع اعتبار الزامی است."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["standard_minutes"].initial = 45
            self.fields["grace_minutes"].initial = 5
            self.fields["rounding_minutes"].initial = 5
            self.fields["max_minutes"].initial = 120
            self.fields["insurance_share"].initial = 0
            self.fields["color"].initial = "#2563eb"
            self.fields["is_active"].initial = True
            self.fields["effective_from"].initial = timezone.localdate()

        self.fields["color"].required = False
        self.fields["effective_to"].required = False
        self.fields["insurance_share"].required = False

    def clean(self):
        cleaned = super().clean()

        standard = cleaned.get("standard_minutes")
        max_min = cleaned.get("max_minutes")
        if standard and max_min and max_min <= standard:
            self.add_error(
                "max_minutes",
                "حداکثر زمان باید بزرگ‌تر از زمان استاندارد باشد.",
            )

        effective_from = cleaned.get("effective_from")
        effective_to = cleaned.get("effective_to")
        if effective_from and effective_to and effective_to < effective_from:
            self.add_error(
                "effective_to",
                "تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.",
            )

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        if not obj.code:
            base_code = self._slugify_name(obj.name)
            obj.code = base_code
            counter = 1
            while ConsultantLevel.objects.filter(code=obj.code).exclude(pk=obj.pk).exists():
                obj.code = f"{base_code}-{counter}"
                counter += 1

        if not obj.order:
            last = ConsultantLevel.objects.order_by("-order").values_list("order", flat=True).first()
            obj.order = (last or 0) + 1

        if commit:
            obj.save()
        return obj

    @staticmethod
    def _slugify_name(name):
        mapping = {
            "کارشناس": "expert",
            "کارشناسی ارشد": "master",
            "دکتری": "phd",
            "فوق تخصص": "specialist",
            "روانپزشک": "psychiatrist",
        }
        if name in mapping:
            return mapping[name]
        count = ConsultantLevel.objects.count() + 1
        return f"level-{count}"