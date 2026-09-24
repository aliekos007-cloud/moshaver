from django.db import models


class ClinicSettings(models.Model):
    """تنظیمات مطب — فقط یک رکورد وجود داره (Singleton)."""

    # ===== اطلاعات پایه مطب =====
    clinic_name = models.CharField("نام مطب", max_length=200, default="مطب طبیب")
    doctor_name = models.CharField("نام پزشک", max_length=200, blank=True)
    specialty = models.CharField("تخصص", max_length=200, blank=True)
    license_number = models.CharField("شماره پروانه", max_length=50, blank=True)
    phone = models.CharField("تلفن", max_length=30, blank=True)
    mobile = models.CharField("همراه", max_length=30, blank=True)
    address = models.TextField("آدرس", blank=True)
    logo = models.ImageField("لوگو", upload_to="clinic/", blank=True, null=True)

    # ===== متن‌های چاپی =====
    footer_note = models.TextField(
        "یادداشت پایین نسخه", blank=True,
        default="این نسخه صرفاً جهت اطلاع و مصرف بیمار صادر شده است.",
    )
    prescription_header = models.TextField(
        "سربرگ نسخه", blank=True,
        help_text="متن ثابتی که در ابتدای نسخه چاپ می‌شود.",
    )

    # ===== نوبت‌دهی و پرداخت =====
    require_payment_for_appointment = models.BooleanField(
        "الزام پرداخت برای نوبت‌ها",
        default=False,
        help_text="اگه فعال باشه، بیماران قبل از نوبت باید مبلغ ویزیت رو پرداخت کنن.",
    )
    default_appointment_fee = models.DecimalField(
        "مبلغ پیش‌فرض ویزیت (تومان)",
        max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text="برای محاسبه‌ی خودکار مبلغ نوبت‌ها",
    )
    appointment_slot_duration = models.PositiveSmallIntegerField(
        "طول پیش‌فرض هر نوبت (دقیقه)",
        default=15,
        help_text="پیش‌فرض: ۱۵ دقیقه برای ویزیت معمولی",
    )

    class Meta:
        verbose_name = "تنظیمات مطب"
        verbose_name_plural = "تنظیمات مطب"

    def __str__(self):
        return self.clinic_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj