from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User, Role


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=6,
        help_text="حداقل ۶ کاراکتر",
    )
    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "national_code", "phone", "role", "is_active")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "national_code": forms.TextInput(attrs={"class": "form-control", "maxlength": 10}),
            "phone": forms.TextInput(attrs={"class": "form-control", "maxlength": 15}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_national_code(self):
        code = self.cleaned_data["national_code"]
        if not code.isdigit():
            raise forms.ValidationError("کد ملی باید فقط شامل اعداد باشد.")
        if len(code) != 10:
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        if User.objects.filter(national_code=code).exists():
            raise forms.ValidationError("این کد ملی قبلاً ثبت شده است.")
        return code

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as e:
                self.add_error("password", e)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "national_code", "phone", "role", "is_active")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "national_code": forms.TextInput(attrs={"class": "form-control", "maxlength": 10}),
            "phone": forms.TextInput(attrs={"class": "form-control", "maxlength": 15}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_national_code(self):
        code = self.cleaned_data["national_code"]
        if not code.isdigit():
            raise forms.ValidationError("کد ملی باید فقط شامل اعداد باشد.")
        if len(code) != 10:
            raise forms.ValidationError("کد ملی باید ۱۰ رقم باشد.")
        if User.objects.filter(national_code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("این کد ملی قبلاً برای کاربر دیگری ثبت شده است.")
        return code


class UserPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=6,
    )
    new_password_confirm = forms.CharField(
        label="تکرار رمز جدید",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("new_password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as e:
                self.add_error("new_password", e)
        return cleaned