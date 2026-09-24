from django.db import models
from .validators import validate_iranian_national_code, validate_iranian_mobile


class Patient(models.Model):
    GENDER = [("M", "مرد"), ("F", "زن")]
    MARITAL = [
        ("single", "مجرد"),
        ("married", "متأهل"),
        ("divorced", "مطلقه"),
        ("widowed", "بیوه"),
    ]

    # ===== اطلاعات هویتی =====
    file_number = models.CharField(
        "شماره پرونده", max_length=20, unique=True,
        blank=True, editable=False,
    )
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    father_name = models.CharField("نام پدر", max_length=100, blank=True)

    national_code = models.CharField(
        "کد ملی", max_length=10, unique=True, blank=False, null=True,
        validators=[validate_iranian_national_code],
        error_messages={
            "unique": "این کد ملی قبلاً برای بیمار دیگری ثبت شده است.",
            "required": "وارد کردن کد ملی الزامی است.",
        },
    )

    is_foreign = models.BooleanField("اتباع خارجی", default=False)
    foreign_id = models.CharField("شماره شناسایی اتباع", max_length=30, blank=True)
    gender = models.CharField("جنسیت", max_length=1, choices=GENDER)
    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)
    marital_status = models.CharField(
        "وضعیت تأهل", max_length=10, choices=MARITAL, blank=True,
    )
    job = models.CharField("شغل", max_length=100, blank=True)
    education = models.CharField("تحصیلات", max_length=100, blank=True)

    # ===== اطلاعات تماس =====
    phone = models.CharField("تلفن", max_length=15, blank=True)
    mobile = models.CharField(
        "تلفن همراه", max_length=15,
        validators=[validate_iranian_mobile],
        error_messages={"required": "وارد کردن شماره موبایل الزامی است."},
    )
    emergency_phone = models.CharField("تلفن اضطراری", max_length=15, blank=True)
    emergency_name = models.CharField("نام فرد اضطراری", max_length=100, blank=True)

    # ===== آدرس =====
    country = models.CharField("کشور", max_length=50, default="ایران")
    province = models.CharField("استان", max_length=50, blank=True)
    city = models.CharField("شهر", max_length=50, blank=True)
    street = models.CharField("خیابان", max_length=100, blank=True)
    alley = models.CharField("کوچه", max_length=100, blank=True)
    plaque = models.CharField("پلاک", max_length=20, blank=True)
    postal_code = models.CharField("کد پستی", max_length=10, blank=True)
    address_note = models.TextField("توضیحات آدرس", blank=True)

    # ===== متادیتا =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "بیمار"
        verbose_name_plural = "بیماران"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["last_name", "first_name"], name="patient_name_idx"),
            models.Index(fields=["mobile"], name="patient_mobile_idx"),
            models.Index(fields=["-created_at"], name="patient_created_idx"),
            models.Index(fields=["last_name"], name="patient_lastname_idx"),
        ]

    def __str__(self):
        return f"{self.file_number} — {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.file_number:
            self.file_number = f"{self.pk:05d}"
            Patient.objects.filter(pk=self.pk).update(file_number=self.file_number)