from django import forms
from django.utils import timezone
from .models import ClinicSettings, Room, ConsultantDailyPresence


class ClinicSettingsForm(forms.ModelForm):
    class Meta:
        model = ClinicSettings
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault("rows", 2)
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "form-check-input")
            else:
                w.attrs.setdefault("class", "form-control")


class RoomForm(forms.ModelForm):
    """فرم ساخت و ویرایش اتاق."""

    class Meta:
        model = Room
        fields = ["name", "capacity", "color", "equipment", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "مثلاً: اتاق ۱",
            }),
            "capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 20,
            }),
            "color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
            "equipment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "مثلاً: پروژکتور، مبل راحتی، میز بازی‌درمانی",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }
        labels = {
            "name": "نام اتاق",
            "capacity": "ظرفیت",
            "color": "رنگ",
            "equipment": "تجهیزات",
            "is_active": "فعال",
        }


# ==================================================
# فرم ثبت حضور مشاور
# ==================================================

class PresenceRegisterForm(forms.Form):
    """ثبت حضور مشاور — صبح که می‌رسد."""

    consultant = forms.ModelChoiceField(
        label="مشاور",
        queryset=None,
        empty_label="— انتخاب کنید —",
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg",
        }),
        error_messages={
            "required": "انتخاب مشاور الزامی است.",
            "invalid_choice": "مشاور انتخاب‌شده معتبر نیست.",
        },
    )

    room = forms.ModelChoiceField(
        label="اتاق فعلی",
        queryset=None,
        empty_label="— بدون اتاق —",
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg",
        }),
    )

    note = forms.CharField(
        label="یادداشت",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "مثلاً: ساعت خروج ۱۲، جلسهٔ فوق‌برنامه",
        }),
    )

    def __init__(self, *args, **kwargs):
        from accounts.models import User, Role
        super().__init__(*args, **kwargs)

        today = timezone.localdate()

        # مشاورانی که امروز حضور ندارن
        present_ids = ConsultantDailyPresence.objects.filter(
            date=today,
        ).values_list("consultant_id", flat=True)

        self.fields["consultant"].queryset = User.objects.filter(
            role=Role.CONSULTANT,
            is_active=True,
        ).exclude(id__in=present_ids).order_by("last_name", "first_name")

        # اتاق‌های فعال
        self.fields["room"].queryset = Room.objects.filter(is_active=True).order_by("order", "name")


class ChangeRoomForm(forms.Form):
    """تغییر اتاق — وسط روز."""

    room = forms.ModelChoiceField(
        label="اتاق جدید",
        queryset=None,
        empty_label="— بدون اتاق —",
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select form-select-lg",
        }),
    )

    note = forms.CharField(
        label="دلیل تغییر",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "مثلاً: جلسهٔ گروهی، تغییر اتاق",
        }),
    )

    def __init__(self, *args, **kwargs):
        current_presence = kwargs.pop("current_presence", None)
        super().__init__(*args, **kwargs)

        qs = Room.objects.filter(is_active=True).order_by("order", "name")
        if current_presence and current_presence.room_id:
            qs = qs.exclude(id=current_presence.room_id)
        self.fields["room"].queryset = qs