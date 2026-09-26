from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from accounts.models import User, Role
from clinic.models import Room
from patients.models import Patient
from .models import Session


# ==================================================
# کلاس پایه برای input زمان ۲۴ ساعته
# ==================================================

class Time24Input(forms.TextInput):
    """input زمان به فرمت ۲۴ ساعته."""
    def __init__(self, attrs=None):
        default_attrs = {
            "class": "form-control time-24",
            "placeholder": "ساعت:دقیقه — مثلاً 14:30",
            "inputmode": "numeric",
            "autocomplete": "off",
            "maxlength": "5",
            "dir": "ltr",
            "style": "text-align: center; font-family: 'Courier New', monospace; letter-spacing: 3px; font-size: 1.1rem; font-weight: 600;",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


# ==================================================
# توابع کمکی
# ==================================================

def _parse_time_input(value):
    """ورودی زمان → فرمت HH:MM."""
    if not value:
        return None

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    for i, d in enumerate(persian_digits):
        value = str(value).replace(d, str(i))

    value = str(value).strip()

    if ':' in value:
        parts = value.split(':')
        try:
            h = int(parts[0]) if parts[0] else 0
            m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
        except (ValueError, IndexError):
            pass

    digits = ''.join(c for c in value if c.isdigit())
    if len(digits) == 4:
        h, m = int(digits[:2]), int(digits[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    elif len(digits) == 3:
        h, m = int(digits[:1]), int(digits[1:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    elif len(digits) <= 2:
        h = int(digits)
        if 0 <= h <= 23:
            return f"{h:02d}:00"

    return None


def _check_self_consultation(client, consultant, form, field_name="consultant"):
    """چک: مراجع و مشاور یک نفر نباشن."""
    if not client or not consultant:
        return

    client_nc = (client.national_code or "").strip()
    consultant_nc = (consultant.national_code or "").strip()

    if client_nc and consultant_nc and client_nc == consultant_nc:
        form.add_error(
            field_name,
            "مشاور نمی‌تواند خودش را به‌عنوان مراجع انتخاب کند. "
            "کد ملی مراجع و مشاور یکسان است."
        )
        return True

    client_full = f"{client.first_name} {client.last_name}".strip()
    consultant_full = f"{consultant.first_name} {consultant.last_name}".strip()
    if client_full and consultant_full and client_full == consultant_full:
        form.add_error(field_name, "مراجع و مشاور نمی‌توانند یک نفر باشند.")
        return True

    return False


# ==================================================
# فرم ساخت جلسه
# ==================================================

class SessionCreateForm(forms.Form):
    """فرم ساخت جلسهٔ جدید."""

    SESSION_TYPE_CHOICES = [
        ("individual", "فردی"),
        ("couple", "زوج"),
        ("family", "خانواده"),
        ("group", "گروه"),
        ("phone", "تلفنی"),
        ("online", "آنلاین"),
    ]

    client = forms.ModelChoiceField(
        label="مراجع",
        queryset=Patient.objects.all().order_by("last_name", "first_name"),
        empty_label="— انتخاب کنید —",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
        error_messages={"required": "انتخاب مراجع الزامی است."},
    )

    consultant = forms.ModelChoiceField(
        label="مشاور",
        queryset=User.objects.filter(
            is_active=True,
            consultant_level__isnull=False,
        ).order_by("last_name", "first_name"),
        empty_label="— انتخاب کنید —",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
        error_messages={"required": "انتخاب مشاور الزامی است."},
    )

    room = forms.ModelChoiceField(
        label="اتاق",
        queryset=Room.objects.filter(is_active=True).order_by("order", "name"),
        empty_label="— انتخاب اتاق —",
        required=True,
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
        error_messages={
            "required": "انتخاب اتاق الزامی است.",
            "invalid_choice": "اتاق انتخاب‌شده معتبر نیست.",
        },
    )

    session_type = forms.ChoiceField(
        label="نوع جلسه",
        choices=SESSION_TYPE_CHOICES,
        initial="individual",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    scheduled_date = forms.DateField(
        label="تاریخ",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
        error_messages={"required": "تاریخ جلسه الزامی است."},
    )

    scheduled_time = forms.TimeField(
        label="ساعت شروع",
        widget=Time24Input(),
        error_messages={"required": "ساعت شروع الزامی است."},
    )

    duration_minutes = forms.IntegerField(
        label="مدت (دقیقه)",
        initial=45,
        min_value=5,
        max_value=240,
        widget=forms.NumberInput(attrs={
            "class": "form-control persian-number",
            "inputmode": "numeric",
        }),
        error_messages={"required": "مدت جلسه الزامی است."},
    )

    secretary_note = forms.CharField(
        label="یادداشت",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "مثلاً: مراجع جدید، جلسهٔ سوم",
        }),
    )

    def __init__(self, *args, **kwargs):
        # ===== پارامتر خاص ما =====
        current_user = kwargs.pop("current_user", None)

        super().__init__(*args, **kwargs)

        self.current_user = current_user

        # ===== مقادیر اولیه =====
        if not self.is_bound:
            now = timezone.localtime()
            if not self.initial.get("scheduled_date"):
                self.initial["scheduled_date"] = now.date()
            if not self.initial.get("scheduled_time"):
                self.initial["scheduled_time"] = now.strftime("%H:%M")

        # ===== اگه کاربر مشاوره، فیلد مشاور رو قفل کن =====
        if current_user and getattr(current_user, "role", None) == "consultant":
            self.fields["consultant"].queryset = User.objects.filter(pk=current_user.pk)
            self.fields["consultant"].initial = current_user
            self.fields["consultant"].disabled = True
            self.fields["consultant"].widget.attrs["style"] = \
                "pointer-events: none; opacity: .85; background: #f8fafc;"

    def clean(self):
        cleaned = super().clean()

        # ===== مشاور نمی‌تونه مشاور انتخاب کنه =====
        if self.current_user and getattr(self.current_user, "role", None) == "consultant":
            cleaned["consultant"] = self.current_user

        client = cleaned.get("client")
        consultant = cleaned.get("consultant")
        room = cleaned.get("room")
        date = cleaned.get("scheduled_date")
        start_time = cleaned.get("scheduled_time")
        duration = cleaned.get("duration_minutes")

        # ===== نرمال‌سازی ساعت =====
        raw_time = cleaned.get("scheduled_time")
        if raw_time and isinstance(raw_time, str):
            parsed = _parse_time_input(raw_time)
            if parsed:
                try:
                    from datetime import time as dt_time
                    h, m = parsed.split(':')
                    cleaned["scheduled_time"] = dt_time(int(h), int(m))
                    start_time = cleaned["scheduled_time"]
                except (ValueError, AttributeError):
                    self.add_error("scheduled_time", "فرمت ساعت نامعتبر است. مثال: 14:30")
                    return cleaned
            else:
                self.add_error("scheduled_time", "فرمت ساعت نامعتبر است. مثال: 14:30")
                return cleaned

        # ===== چک: مراجع و مشاور یک نفر نباشن =====
        _check_self_consultation(client, consultant, self)

        # ===== چک تاریخ و ساعت گذشته =====
        if date and start_time:
            candidate_dt = timezone.make_aware(datetime.combine(date, start_time))
            now = timezone.localtime()
            if candidate_dt < (now - timedelta(minutes=5)):
                self.add_error(
                    "scheduled_time",
                    "زمان انتخابی گذشته است. لطفاً زمان آینده انتخاب کنید."
                )

        if not consultant or not date or not start_time or not duration:
            return cleaned

        start_dt = timezone.make_aware(datetime.combine(date, start_time))
        end_dt = start_dt + timedelta(minutes=duration)

        cleaned["start_dt"] = start_dt
        cleaned["end_dt"] = end_dt

        # ===== تداخل مشاور =====
        conflict = Session.objects.filter(
            consultant=consultant,
            status__in=["scheduled", "in_progress", "paused"],
            scheduled_start__lt=end_dt,
            scheduled_end__gt=start_dt,
        ).exists()
        if conflict:
            self.add_error(
                "scheduled_time",
                "این زمان با جلسهٔ دیگری از این مشاور تداخل دارد."
            )

        # ===== چک: مشاور الان در جلسهٔ فعال نباشه =====
        active_now = Session.objects.filter(
            consultant=consultant,
            status__in=["in_progress", "paused"],
        ).first()
        if active_now:
            self.add_error(
                "consultant",
                f"«{consultant.get_full_name()}» در حال حاضر در جلسه‌ای با "
                f"{active_now.client.full_name} است."
            )

        # ===== تداخل اتاق =====
        if room:
            room_conflict = Session.objects.filter(
                room=room,
                status__in=["scheduled", "in_progress", "paused"],
                scheduled_start__lt=end_dt,
                scheduled_end__gt=start_dt,
            ).exists()
            if room_conflict:
                self.add_error("room", "این اتاق در این زمان اشغال است.")

        # ===== چک سطح مشاور =====
        if consultant and not consultant.consultant_level:
            self.add_error(
                "consultant",
                "این مشاور سطح تعریف‌شده ندارد. ابتدا سطح او را تنظیم کنید."
            )

        return cleaned

    def save(self):
        cleaned = self.cleaned_data
        consultant = cleaned["consultant"]

        session = Session.objects.create(
            client=cleaned["client"],
            consultant=consultant,
            room=cleaned.get("room"),
            level_snapshot=consultant.consultant_level.snapshot(),
            scheduled_start=cleaned["start_dt"],
            scheduled_end=cleaned["end_dt"],
            session_type=cleaned["session_type"],
            secretary_note=cleaned.get("secretary_note", ""),
            status="scheduled",
        )

        prev_count = Session.objects.filter(
            client=session.client,
        ).exclude(pk=session.pk).count()
        session.session_number = prev_count + 1
        session.save(update_fields=["session_number"])

        return session


# ==================================================
# فرم ویرایش جلسه
# ==================================================

class SessionEditForm(forms.ModelForm):
    """فرم ویرایش جلسه."""

    scheduled_date = forms.DateField(
        label="تاریخ",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
        error_messages={"required": "تاریخ جلسه الزامی است."},
    )

    scheduled_start_time = forms.TimeField(
        label="ساعت شروع",
        widget=Time24Input(),
        error_messages={"required": "ساعت شروع الزامی است."},
    )

    duration_minutes = forms.IntegerField(
        label="مدت (دقیقه)",
        min_value=5,
        max_value=240,
        widget=forms.NumberInput(attrs={
            "class": "form-control persian-number",
            "inputmode": "numeric",
        }),
        error_messages={"required": "مدت جلسه الزامی است."},
    )

    class Meta:
        model = Session
        fields = [
            "consultant",
            "room",
            "session_type",
            "secretary_note",
        ]
        widgets = {
            "consultant": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "room": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "session_type": forms.Select(attrs={"class": "form-select"}),
            "secretary_note": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "توضیحات",
            }),
        }
        labels = {
            "consultant": "مشاور",
            "room": "اتاق",
            "session_type": "نوع جلسه",
            "secretary_note": "یادداشت",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["consultant"].queryset = User.objects.filter(
            is_active=True,
            consultant_level__isnull=False,
        ).order_by("last_name", "first_name")

        self.fields["room"].queryset = Room.objects.filter(
            is_active=True,
        ).order_by("order", "name")

        # اتاق اجباری
        self.fields["room"].required = True

        if self.instance.pk and self.instance.scheduled_start:
            local_start = timezone.localtime(self.instance.scheduled_start)
            local_end = timezone.localtime(self.instance.scheduled_end)

            self.initial["scheduled_date"] = local_start.date()
            self.initial["scheduled_start_time"] = local_start.strftime("%H:%M")

            delta = local_end - local_start
            self.initial["duration_minutes"] = int(delta.total_seconds() // 60)

    def clean(self):
        cleaned = super().clean()

        consultant = cleaned.get("consultant")
        room = cleaned.get("room")
        date = cleaned.get("scheduled_date")
        start_time = cleaned.get("scheduled_start_time")
        duration = cleaned.get("duration_minutes")

        # ===== نرمال‌سازی ساعت =====
        raw_time = cleaned.get("scheduled_start_time")
        if raw_time and isinstance(raw_time, str):
            parsed = _parse_time_input(raw_time)
            if parsed:
                try:
                    from datetime import time as dt_time
                    h, m = parsed.split(':')
                    cleaned["scheduled_start_time"] = dt_time(int(h), int(m))
                    start_time = cleaned["scheduled_start_time"]
                except (ValueError, AttributeError):
                    self.add_error("scheduled_start_time", "فرمت ساعت نامعتبر است.")
                    return cleaned
            else:
                self.add_error("scheduled_start_time", "فرمت ساعت نامعتبر است.")
                return cleaned

        # ===== چک: مراجع و مشاور =====
        if self.instance.pk:
            _check_self_consultation(self.instance.client, consultant, self)

        # ===== چک تاریخ و ساعت گذشته =====
        if date and start_time and self.instance.pk:
            candidate_dt = timezone.make_aware(datetime.combine(date, start_time))
            now = timezone.localtime()
            original_dt = timezone.localtime(self.instance.scheduled_start)

            if candidate_dt != original_dt and candidate_dt < (now - timedelta(minutes=5)):
                self.add_error(
                    "scheduled_start_time",
                    "زمان انتخابی گذشته است. لطفاً زمان آینده انتخاب کنید."
                )

        if not consultant or not date or not start_time or not duration:
            return cleaned

        start_dt = timezone.make_aware(datetime.combine(date, start_time))
        end_dt = start_dt + timedelta(minutes=duration)

        cleaned["start_dt"] = start_dt
        cleaned["end_dt"] = end_dt

        # ===== تداخل مشاور =====
        conflict_qs = Session.objects.filter(
            consultant=consultant,
            status__in=["scheduled", "in_progress", "paused"],
            scheduled_start__lt=end_dt,
            scheduled_end__gt=start_dt,
        ).exclude(pk=self.instance.pk)

        if conflict_qs.exists():
            self.add_error(
                "scheduled_start_time",
                "این زمان با جلسهٔ دیگری از این مشاور تداخل دارد."
            )

        # ===== تداخل اتاق =====
        if room:
            room_conflict = Session.objects.filter(
                room=room,
                status__in=["scheduled", "in_progress", "paused"],
                scheduled_start__lt=end_dt,
                scheduled_end__gt=start_dt,
            ).exclude(pk=self.instance.pk)

            if room_conflict.exists():
                self.add_error("room", "این اتاق در این زمان اشغال است.")

        # ===== چک سطح مشاور =====
        if consultant and not consultant.consultant_level:
            self.add_error(
                "consultant",
                "این مشاور سطح تعریف‌شده ندارد. ابتدا سطح او را تنظیم کنید."
            )

        return cleaned

    def save(self, commit=True):
        session = super().save(commit=False)

        session.scheduled_start = self.cleaned_data["start_dt"]
        session.scheduled_end = self.cleaned_data["end_dt"]

        if session.consultant and session.consultant.consultant_level:
            session.level_snapshot = session.consultant.consultant_level.snapshot()

        if commit:
            session.save()
        return session