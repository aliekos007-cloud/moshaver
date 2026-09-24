from datetime import datetime

from django import forms
from .models import WeeklySchedule, TimeOff, Appointment


def _style(form):
    for name, field in form.fields.items():
        w = field.widget
        if isinstance(w, forms.Textarea):
            w.attrs.setdefault("rows", 2)
            w.attrs.setdefault("class", "form-control")
        elif isinstance(w, forms.Select):
            w.attrs.setdefault("class", "form-select")
        elif isinstance(w, forms.CheckboxInput):
            w.attrs.setdefault("class", "form-check-input")
        elif isinstance(w, forms.HiddenInput):
            continue
        elif isinstance(w, forms.TimeInput):
            w.attrs.setdefault("class", "form-control")
            w.attrs["type"] = "time"
        else:
            w.attrs.setdefault("class", "form-control")
    return form


class WeeklyScheduleForm(forms.ModelForm):
    class Meta:
        model = WeeklySchedule
        fields = ("physician", "day_of_week", "start_time", "end_time",
                  "slot_duration", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["physician"].queryset = self.fields["physician"].queryset.filter(
            role__in=["physician", "manager"]
        )
        _style(self)


class TimeOffForm(forms.ModelForm):
    class Meta:
        model = TimeOff
        fields = ("physician", "date", "all_day", "start_time", "end_time",
                  "reason", "note")
        widgets = {
            "date": forms.HiddenInput(attrs={"id": "id_time_off_date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["physician"].queryset = self.fields["physician"].queryset.filter(
            role__in=["physician", "manager"]
        )
        self.fields["start_time"].required = False
        self.fields["end_time"].required = False
        _style(self)

    def clean(self):
        cleaned = super().clean()
        all_day = cleaned.get("all_day")
        if not all_day:
            if not cleaned.get("start_time") or not cleaned.get("end_time"):
                raise forms.ValidationError("برای مرخصی ساعتی، ساعت شروع و پایان الزامی است.")
            if cleaned["start_time"] >= cleaned["end_time"]:
                raise forms.ValidationError("ساعت شروع باید قبل از ساعت پایان باشد.")
        return cleaned


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("patient", "physician", "date", "start_time", "end_time",
                  "status", "source", "reason", "note")
        widgets = {
            "date": forms.HiddenInput(attrs={"id": "id_appointment_date"}),
            "start_time": forms.HiddenInput(attrs={"id": "id_start_time"}),
            "end_time": forms.HiddenInput(attrs={"id": "id_end_time"}),
            "reason": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)

        if patient:
            self.fields["patient"].initial = patient

        from patients.models import Patient
        self.fields["patient"].queryset = Patient.objects.all()[:1000]
        self.fields["patient"].required = True
        self.fields["patient"].empty_label = "— انتخاب مراجع —"

        self.fields["physician"].queryset = self.fields["physician"].queryset.filter(
            role__in=["physician", "manager"]
        )
        self.fields["physician"].empty_label = "— انتخاب طبیب —"

        self.fields["status"].choices = [
            ("scheduled", "برنامه‌ریزی‌شده"),
            ("confirmed", "تأیید شده"),
        ]

        _style(self)

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        st = cleaned.get("start_time")
        et = cleaned.get("end_time")
        physician = cleaned.get("physician")

        if date and st and et:
            if st >= et:
                raise forms.ValidationError("ساعت شروع باید قبل از پایان باشد.")

            conflicts = Appointment.objects.filter(
                physician=physician,
                date=date,
                status__in=["scheduled", "confirmed", "arrived", "in_progress"],
            ).filter(
                start_time__lt=et,
                end_time__gt=st,
            ).exclude(pk=self.instance.pk if self.instance else None)

            if conflicts.exists():
                c = conflicts.first()
                raise forms.ValidationError(
                    f"این زمان با نوبت {c.patient.full_name} در ساعت {c.start_time:%H:%M} تداخل دارد."
                )
        return cleaned


class AppointmentPaymentForm(forms.ModelForm):
    """فرم ثبت پرداخت نوبت — برای استفاده در پنل ادمین یا صفحه‌ی اختصاصی."""
    class Meta:
        model = Appointment
        fields = ("payment_status", "payment_amount", "payment_method", "transaction_id")
        widgets = {
            "payment_amount": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)