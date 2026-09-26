from django.conf import settings
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
    REFERRAL_SOURCES = [
        ("self", "خودمعرف"),
        ("friend", "معرفی دوست / آشنا"),
        ("doctor", "پزشک"),
        ("internet", "اینترنت"),
        ("instagram", "شبکه‌های اجتماعی"),
        ("school", "مدرسه / دانشگاه"),
        ("court", "دادگاه / ارجاع قضایی"),
        ("insurance", "بیمه"),
        ("other", "سایر"),
    ]
    CONFIDENTIALITY_LEVELS = [
        ("normal", "عادی"),
        ("confidential", "محرمانه"),
        ("special", "ویژه"),
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
            "unique": "این کد ملی قبلاً برای مراجع دیگری ثبت شده است.",
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
    district = models.CharField("منطقه / محله", max_length=50, blank=True)
    street = models.CharField("خیابان", max_length=100, blank=True)
    alley = models.CharField("کوچه", max_length=100, blank=True)
    plaque = models.CharField("پلاک", max_length=20, blank=True)
    postal_code = models.CharField("کد پستی", max_length=10, blank=True)
    address_note = models.TextField("توضیحات آدرس", blank=True)

    # ===== ویژهٔ مرکز مشاوره =====
    referral_source = models.CharField(
        "منبع آشنایی", max_length=20,
        choices=REFERRAL_SOURCES, blank=True,
    )
    guardian_name = models.CharField(
        "نام سرپرست / ولی", max_length=100, blank=True,
        help_text="برای مراجعین زیر ۱۸ سال الزامی است",
    )
    guardian_phone = models.CharField(
        "تلفن سرپرست", max_length=15, blank=True,
    )
    confidentiality_level = models.CharField(
        "سطح محرمانگی", max_length=20,
        choices=CONFIDENTIALITY_LEVELS, default="normal",
    )
    assigned_consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_clients",
        verbose_name="مشاور اصلی",
    )

    # ===== مالی =====
    outstanding_balance = models.DecimalField(
        "مانده بدهی (تومان)", max_digits=12, decimal_places=0, default=0,
        help_text="مجموع بدهی انباشته",
    )
    credit_limit = models.DecimalField(
        "سقف اعتبار (تومان)", max_digits=12, decimal_places=0, default=0,
        help_text="۰ = بدون سقف",
    )

    # ===== متادیتا =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مراجع"
        verbose_name_plural = "مراجعین"
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

    @property
    def age(self):
        if not self.birth_date:
            return None
        from django.utils import timezone
        today = timezone.localdate()
        return (
            today.year - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def is_minor(self):
        age = self.age
        return age is not None and age < 18

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.file_number:
            self.file_number = f"{self.pk:05d}"
            Patient.objects.filter(pk=self.pk).update(file_number=self.file_number)


# ==================================================
# شرح حال محرمانه
# ==================================================

class ClientNarrative(models.Model):
    """شرح حال بالینی — فقط مشاور و مدیر ارشد."""
    SUICIDE_RISK = [
        ("none", "بدون خطر"),
        ("low", "کم"),
        ("moderate", "متوسط"),
        ("high", "بالا"),
    ]

    client = models.OneToOneField(
        Patient, on_delete=models.CASCADE,
        related_name="narrative", verbose_name="مراجع",
    )

    chief_complaint = models.TextField("شکایت اصلی")
    history_of_present_illness = models.TextField("تاریخچهٔ مشکل فعلی")

    past_psychiatric_history = models.TextField("سابقهٔ روان‌پزشکی", blank=True)
    family_history = models.TextField("سابقهٔ خانوادگی", blank=True)
    medical_history = models.TextField("سابقهٔ پزشکی", blank=True)
    medications = models.TextField("داروهای مصرفی", blank=True)
    substance_use = models.TextField("مصرف مواد", blank=True)

    social_history = models.TextField("وضعیت اجتماعی", blank=True)
    education_occupation = models.TextField("تحصیلات و شغل", blank=True)
    marital_family_status = models.TextField("وضعیت تأهل و خانواده", blank=True)

    suicide_risk = models.CharField(
        "خطر خودکشی", max_length=20,
        choices=SUICIDE_RISK, default="none",
    )
    self_harm_risk = models.CharField(
        "خطر خودآسیبی", max_length=20,
        choices=SUICIDE_RISK, default="none",
    )
    risk_notes = models.TextField("یادداشت خطر", blank=True)

    provisional_diagnosis = models.TextField("تشخیص اولیه", blank=True)
    dsm_codes = models.JSONField("کدهای DSM-5", default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="narratives_created", verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="narratives_updated", verbose_name="آخرین ویرایش‌کننده",
    )

    class Meta:
        verbose_name = "شرح حال"
        verbose_name_plural = "شرح حال‌ها"

    def __str__(self):
        return f"شرح حال — {self.client.full_name}"

    @property
    def has_risk(self):
        return self.suicide_risk != "none" or self.self_harm_risk != "none"