from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from accounts.models import User, Role
from clinic.models import Room
from patients.models import Patient
from .models import Session


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
            role=Role.CONSULTANT,
            is_active=True,
        ).order_by("last_name", "first_name"),
        empty_label="— انتخاب کنید —",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
        error_messages={"required": "انتخاب مشاور الزامی است."},
    )

    room = forms.ModelChoiceField(
        label="اتاق",
        queryset=Room.objects.filter(is_active=True).order_by("order", "name"),
        empty_label="— بدون اتاق —",
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
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
        widget=forms.TimeInput(attrs={
            "class": "form-control",
            "type": "time",
        }),
        error_messages={"required": "ساعت شروع الزامی است."},
    )

    duration_minutes = forms.IntegerField(
        label="مدت (دقیقه)",
        initial=50,
        min_value=5,
        max_value=240,
        widget=forms.NumberInput(attrs={
            "class": "form-control persian-number",
            "inputmode": "numeric",
        }),
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
        # مقدار پیش‌فرض: الان
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            now = timezone.localtime()
            self.fields["scheduled_date"].initial = now.date()
            self.fields["scheduled_time"].initial = now.strftime("%H:%M")

    def clean(self):
        cleaned = super().clean()

        consultant = cleaned.get("consultant")
        room = cleaned.get("room")
        date = cleaned.get("scheduled_date")
        start_time = cleaned.get("scheduled_time")
        duration = cleaned.get("duration_minutes")

        if not consultant or not date or not start_time or not duration:
            return cleaned

        # ساخت datetime
        start_dt = timezone.make_aware(datetime.combine(date, start_time))
        end_dt = start_dt + timedelta(minutes=duration)

        cleaned["start_dt"] = start_dt
        cleaned["end_dt"] = end_dt

        # تداخل مشاور
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

        # تداخل اتاق
        if room:
            room_conflict = Session.objects.filter(
                room=room,
                status__in=["scheduled", "in_progress", "paused"],
                scheduled_start__lt=end_dt,
                scheduled_end__gt=start_dt,
            ).exists()
            if room_conflict:
                self.add_error(
                    "room",
                    "این اتاق در این زمان اشغال است."
                )

        # چک سطح مشاور
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

        # شمارهٔ جلسه
        prev_count = Session.objects.filter(
            client=session.client,
        ).exclude(pk=session.pk).count()
        session.session_number = prev_count + 1
        session.save(update_fields=["session_number"])

        return session