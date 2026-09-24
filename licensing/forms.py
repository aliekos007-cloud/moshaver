from datetime import date, timedelta

from django import forms
from .models import License


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
        else:
            w.attrs.setdefault("class", "form-control")
    return form


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = (
            "licensed_to", "licensed_email", "licensed_phone",
            "tier", "valid_from", "valid_until",
            "max_users", "max_physicians", "max_branches",
            "enable_inventory", "enable_finance", "enable_therapies",
            "enable_documents", "enable_consent", "enable_reports",
            "enable_backup", "enable_audit", "enable_appointments",
            "version", "notes",
        )
        widgets = {
            "valid_from": forms.HiddenInput(),
            "valid_until": forms.HiddenInput(),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["valid_from"].required = False
        self.fields["valid_until"].required = False

        # پیش‌فرض: از امروز تا یک سال
        if not self.instance.pk:
            self.fields["valid_from"].initial = date.today().isoformat()
            self.fields["valid_until"].initial = (date.today() + timedelta(days=365)).isoformat()

        _style(self)


class ActivateLicenseForm(forms.Form):
    """فرم فعال‌سازی با کلید لایسنس."""
    license_key = forms.CharField(
        label="کلید لایسنس",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg text-center",
            "placeholder": "TABIB-XXXX-XXXX-XXXX-XXXX",
            "style": "direction: ltr; letter-spacing: 2px; font-family: monospace;",
            "autocomplete": "off",
        }),
    )

    def clean_license_key(self):
        key = self.cleaned_data["license_key"].strip().upper()
        # نرمال‌سازی
        key = key.replace(" ", "")
        return key