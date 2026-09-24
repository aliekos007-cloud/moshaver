from django import forms
from .models import Visit


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = (
            "chief_complaint", "history", "brief_history",
            "diagnosis", "treatment_plan", "follow_up",
        )
        widgets = {
            "chief_complaint": forms.Textarea(attrs={"rows": 3, "placeholder": "علت مراجعه بیمار..."}),
            "history": forms.Textarea(attrs={"rows": 3, "placeholder": "شرح حال کامل..."}),
            "brief_history": forms.Textarea(attrs={"rows": 2, "placeholder": "خلاصه‌ای از بیماری..."}),
            "diagnosis": forms.Textarea(attrs={"rows": 3, "placeholder": "تشخیص پزشک..."}),
            "treatment_plan": forms.Textarea(attrs={"rows": 3, "placeholder": "برنامه درمان..."}),
            "follow_up": forms.Textarea(attrs={"rows": 2, "placeholder": "نتیجه پیگیری..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")