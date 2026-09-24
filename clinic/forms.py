from django import forms
from .models import ClinicSettings, Room


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