from django import forms
from .models import ClinicSettings


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