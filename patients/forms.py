from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = (
            "file_number",
            "created_at",
            "updated_at",
            # فیلدهای سیستمی — در فرم نمایش داده نمی‌شن
            "country",
            "confidentiality_level",
            "outstanding_balance",
            "credit_limit",
            "assigned_consultant",
            "is_foreign",
            "foreign_id",
        )
        widgets = {
            "birth_date": forms.HiddenInput(attrs={"id": "id_birth_date_gregorian"}),
        }
        error_messages = {
            "national_code": {
                "unique": "این کد ملی قبلاً برای مراجع دیگری ثبت شده است.",
                "required": "وارد کردن کد ملی الزامی است.",
            },
            "mobile": {
                "required": "وارد کردن شماره موبایل الزامی است.",
            },
            "first_name": {
                "required": "وارد کردن نام الزامی است.",
            },
            "last_name": {
                "required": "وارد کردن نام خانوادگی الزامی است.",
            },
            "gender": {
                "required": "انتخاب جنسیت الزامی است.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # فیلدهای اجباری
        required_fields = ["first_name", "last_name", "gender", "mobile", "national_code"]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True

        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "form-check-input")
            elif isinstance(w, forms.HiddenInput):
                continue
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "form-select")
            else:
                w.attrs.setdefault("class", "form-control")
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault("rows", 2)

            if name == "gender":
                field.choices = [("", "انتخاب جنسیت...")] + [c for c in field.choices if c[0]]
            elif name == "marital_status":
                field.choices = [("", "انتخاب وضعیت...")] + [c for c in field.choices if c[0]]