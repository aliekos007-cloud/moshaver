from django.conf import settings
from django.db import models


class ClinicSettings(models.Model):
    """تنظیمات مرکز مشاوره — فقط یک رکورد وجود داره (Singleton)."""

    # ===== اطلاعات پایه =====
    clinic_name = models.CharField("نام مرکز", max_length=200, default="مرکز مشاوره")
    manager_name = models.CharField("نام مدیر", max_length=200, blank=True)
    specialty = models.CharField("تخصص / رویکرد", max_length=200, blank=True)
    license_number = models.CharField("شماره پروانه", max_length=50, blank=True)
    phone = models.CharField("تلفن", max_length=30, blank=True)
    mobile = models.CharField("همراه", max_length=30, blank=True)
    address = models.TextField("آدرس", blank=True)
    logo = models.ImageField("لوگو", upload_to="clinic/", blank=True, null=True)

    # ===== متن‌های چاپی =====
    footer_note = models.TextField(
        "یادداشت پایین فاکتور", blank=True,
        default="از اعتماد شما سپاسگزاریم.",
    )
    invoice_header = models.TextField(
        "سربرگ فاکتور", blank=True,
        help_text="متن ثابتی که در ابتدای فاکتور چاپ می‌شود.",
    )

    # ===== نوبت‌دهی و پرداخت =====
    require_payment_for_appointment = models.BooleanField(
        "الزام پرداخت برای نوبت‌ها",
        default=False,
        help_text="اگه فعال باشه، مراجعین قبل از نوبت باید مبلغ مشاوره رو پرداخت کنن.",
    )
    default_appointment_fee = models.DecimalField(
        "مبلغ پیش‌فرض مشاوره (تومان)",
        max_digits=14, decimal_places=0,
        null=True, blank=True,
        help_text="برای محاسبه‌ی خودکار مبلغ نوبت‌ها",
    )
    appointment_slot_duration = models.PositiveSmallIntegerField(
        "طول پیش‌فرض هر جلسه (دقیقه)",
        default=50,
        help_text="پیش‌فرض: ۵۰ دقیقه برای جلسهٔ مشاوره",
    )

    # ===== بازهٔ رزرو =====
    booking_horizon_months = models.PositiveSmallIntegerField(
        "بازهٔ مجاز رزرو (ماه)",
        default=6,
        help_text="چند ماه جلوتر می‌توان نوبت گرفت",
    )

    class Meta:
        verbose_name = "تنظیمات مرکز"
        verbose_name_plural = "تنظیمات مرکز"

    def __str__(self):
        return self.clinic_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ==================================================
# اتاق‌های مشاوره
# ==================================================

class Room(models.Model):
    """اتاق‌های مشاوره — چون اتاق‌ها چرخشی هستند."""
    name = models.CharField("نام اتاق", max_length=50)
    code = models.SlugField(
        "کد داخلی", max_length=50, unique=True,
        blank=True, editable=False,
    )
    capacity = models.PositiveIntegerField("ظرفیت", default=1)
    color = models.CharField("رنگ", max_length=7, default="#06b6d4")
    equipment = models.TextField(
        "تجهیزات", blank=True,
        help_text="مثلاً: پروژکتور، مبل راحتی، میز بازی‌درمانی",
    )
    order = models.PositiveIntegerField("ترتیب", default=0, db_index=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "اتاق"
        verbose_name_plural = "اتاق‌ها"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.order:
            last = Room.objects.order_by("-order").values_list("order", flat=True).first()
            self.order = (last or 0) + 1
        super().save(*args, **kwargs)
        if is_new and not self.code:
            self.code = f"room-{self.pk}"
            Room.objects.filter(pk=self.pk).update(code=self.code)


# ==================================================
# حضور روزانه مشاور
# ==================================================

class ConsultantDailyPresence(models.Model):
    """
    حضور روزانهٔ مشاور — هر روز صبح توسط منشی ثبت می‌شود.
    اتاق هم اینجا مشخص می‌شود (چون چرخشی است).
    """

    STATUS_CHOICES = [
        ("present", "حاضر"),
        ("in_session", "در جلسه"),
        ("on_break", "استراحت"),
        ("left", "رفته"),
    ]

    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="daily_presences", verbose_name="مشاور",
    )
    date = models.DateField("تاریخ", db_index=True)
    room = models.ForeignKey(
        Room, null=True, blank=True, on_delete=models.PROTECT,
        related_name="presences", verbose_name="اتاق فعلی",
    )

    arrived_at = models.DateTimeField("ساعت ورود")
    left_at = models.DateTimeField("ساعت خروج", null=True, blank=True)

    status = models.CharField(
        "وضعیت", max_length=20,
        choices=STATUS_CHOICES, default="present",
    )
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "حضور روزانه"
        verbose_name_plural = "حضورهای روزانه"
        unique_together = [("consultant", "date")]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["room", "date"]),
        ]

    def __str__(self):
        return f"{self.consultant.get_full_name()} — {self.date} ({self.get_status_display()})"

    @property
    def is_present(self):
        return self.status in ("present", "in_session", "on_break")


# ==================================================
# تاریخچه تغییر اتاق
# ==================================================

class ConsultantRoomChange(models.Model):
    """تاریخچهٔ تغییر اتاق در یک روز."""
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="room_changes", verbose_name="مشاور",
    )
    date = models.DateField("تاریخ", db_index=True)
    from_room = models.ForeignKey(
        Room, null=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="از اتاق",
    )
    to_room = models.ForeignKey(
        Room, on_delete=models.PROTECT,
        related_name="+", verbose_name="به اتاق",
    )
    changed_at = models.DateTimeField("زمان تغییر")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="room_changes_made", verbose_name="تغییردهنده",
    )
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "تغییر اتاق"
        verbose_name_plural = "تغییرات اتاق"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["consultant", "date", "-changed_at"]),
        ]

    def __str__(self):
        return f"{self.consultant.get_full_name()} — {self.from_room} → {self.to_room}"