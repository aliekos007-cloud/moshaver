from django import forms
from .models import Patient
from .iran_locations import get_provinces, get_cities, get_districts


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = (
            "file_number", "created_at", "updated_at", "country",
            "confidentiality_level", "outstanding_balance", "credit_limit",
            "assigned_consultant", "is_foreign", "foreign_id",
        )
        widgets = {
            "birth_date": forms.HiddenInput(attrs={"id": "id_birth_date_gregorian"}),
            "address_note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
        error_messages = {
            "national_code": {
                "unique": "این کد ملی قبلاً برای مراجع دیگری ثبت شده است.",
                "required": "وارد کردن کد ملی الزامی است.",
            },
            "mobile": {"required": "وارد کردن شماره موبایل الزامی است."},
            "first_name": {"required": "وارد کردن نام الزامی است."},
            "last_name": {"required": "وارد کردن نام خانوادگی الزامی است."},
            "gender": {"required": "انتخاب جنسیت الزامی است."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # فیلدهای اجباری
        required_fields = ["first_name", "last_name", "gender", "mobile", "national_code"]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True

        # اعمال کلاس‌های CSS
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

        # ===== استان =====
        provinces = get_provinces()
        current_province = self.data.get("province") or (self.instance.province if self.instance.pk else "")
        province_choices = [("", "— انتخاب استان —")] + [(p, p) for p in provinces]
        self.fields["province"] = forms.ChoiceField(
            label="استان", choices=province_choices, required=False,
            widget=forms.Select(attrs={"class": "form-select", "id": "id_province"}),
        )
        if current_province in provinces:
            self.initial["province"] = current_province

        # ===== شهر =====
        current_city = self.data.get("city") or (self.instance.city if self.instance.pk else "")
        city_choices = [("", "— ابتدا استان را انتخاب کنید —")]
        if current_province:
            city_choices = [("", "— انتخاب شهر —")] + [(c, c) for c in get_cities(current_province)]
        self.fields["city"] = forms.ChoiceField(
            label="شهر", choices=city_choices, required=False,
            widget=forms.Select(attrs={"class": "form-select", "id": "id_city"}),
        )
        if current_city:
            self.initial["city"] = current_city

        # ===== منطقه (با قابلیت ورود دستی) =====
        current_district = self.data.get("district") or (self.instance.district if self.instance.pk else "")
        district_choices = [("", "— ابتدا شهر را انتخاب کنید —")]
        if current_province and current_city:
            districts = get_districts(current_province, current_city)
            if districts:
                district_choices = [("", "— انتخاب منطقه —")] + [(d, d) for d in districts]
        district_choices.append(("__other__", "✏️ سایر (دستی وارد کنید)"))
        self.fields["district"] = forms.ChoiceField(
            label="منطقه / محله", choices=district_choices, required=False,
            widget=forms.Select(attrs={"class": "form-select", "id": "id_district"}),
        )
        if current_district:
            self.initial["district"] = current_district

        # فیلد دستی منطقه
        self.fields["district_manual"] = forms.CharField(
            label="منطقه (دستی)", required=False,
            widget=forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_district_manual",
                "placeholder": "نام منطقه یا محله را وارد کنید",
                "style": "display: none;",
            }),
        )
        if current_district:
            self.initial["district_manual"] = current_district

    def clean(self):
        cleaned = super().clean()
        district = cleaned.get("district")
        if district == "__other__":
            manual = cleaned.get("district_manual")
            cleaned["district"] = manual if manual else ""
        return cleaned