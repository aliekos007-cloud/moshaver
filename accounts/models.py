from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    CONSULTANT = "consultant", "مشاور"
    SECRETARY  = "secretary",  "منشی"
    MANAGER    = "manager",    "مدیر مرکز"


class UserManager(BaseUserManager):
    def create_user(self, national_code, password=None, **extra):
        if not national_code:
            raise ValueError("کد ملی الزامی است")
        user = self.model(national_code=national_code, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_code, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.MANAGER)
        return self.create_user(national_code, password, **extra)


class User(AbstractUser):
    username = None
    first_name = models.CharField("نام", max_length=100)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    national_code = models.CharField("کد ملی", max_length=10, unique=True)
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.SECRETARY)
    phone = models.CharField("تلفن همراه", max_length=15, blank=True)

    # ===== جدید: اطلاعات مشاور =====
    consultant_level = models.ForeignKey(
        "ConsultantLevel",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="consultants",
        verbose_name="سطح مشاور",
        help_text="فقط برای نقش مشاور پر می‌شود",
    )
    bio = models.TextField("رزومه", blank=True)
    specialties = models.JSONField("تخصص‌ها", default=list, blank=True)

    USERNAME_FIELD = "national_code"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return f"{self.get_full_name()} — {self.get_role_display()}"

    @property
    def is_consultant(self):
        return self.role == Role.CONSULTANT

    @property
    def is_secretary(self):
        return self.role == Role.SECRETARY

    @property
    def is_manager(self):
        return self.role == Role.MANAGER


# ==================================================
# سطح مشاور — تعیین‌کنندهٔ تعرفه
# ==================================================

class ConsultantLevel(models.Model):
    """
    سطح مشاور — تعیین‌کنندهٔ تعرفه
    مثل: کارشناس، کارشناسی ارشد، دکتری، فوق‌تخصص
    """
    name = models.CharField("عنوان سطح", max_length=50)
    code = models.SlugField("کد", unique=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    # ===== تعرفه =====
    standard_minutes = models.PositiveIntegerField(
        "زمان استاندارد (دقیقه)", default=45,
    )
    base_price = models.DecimalField(
        "مبلغ پایه (تومان)", max_digits=12, decimal_places=0,
        help_text="مبلغ جلسهٔ استاندارد",
    )
    overtime_per_minute = models.DecimalField(
        "هزینهٔ هر دقیقهٔ مازاد (تومان)", max_digits=12, decimal_places=0,
    )
    grace_minutes = models.PositiveIntegerField(
        "دقایق ارفاق", default=5,
        help_text="دقایق اول بعد از استاندارد که رایگان است",
    )
    rounding_minutes = models.PositiveIntegerField(
        "رُند کردن (دقیقه)", default=5,
        help_text="۰ = بدون رُند، ۵ = هر ۵ دقیقه یک پله",
    )
    max_minutes = models.PositiveIntegerField(
        "حداکثر زمان مجاز (دقیقه)", default=120,
    )

    # ===== بیمه =====
    insurance_share = models.DecimalField(
        "سهم بیمه (تومان)", max_digits=12, decimal_places=0, default=0,
    )

    # ===== تاریخ اعتبار =====
    effective_from = models.DateField("از تاریخ")
    effective_to = models.DateField("تا تاریخ", null=True, blank=True)

    # ===== نمایش =====
    color = models.CharField("رنگ", max_length=7, default="#2563eb")
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "سطح مشاور"
        verbose_name_plural = "سطوح مشاور"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} — {self.base_price:,} تومان"

    def snapshot(self):
        """اسنپ‌شات برای ذخیره در Session"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "standard_minutes": self.standard_minutes,
            "base_price": int(self.base_price),
            "overtime_per_minute": int(self.overtime_per_minute),
            "grace_minutes": self.grace_minutes,
            "rounding_minutes": self.rounding_minutes,
            "max_minutes": self.max_minutes,
            "color": self.color,
        }


# ==================================================
# برنامهٔ هفتگی مشاور
# ==================================================

class ConsultantWeeklySchedule(models.Model):
    """الگوی هفتگی — «من هر شنبه ۸ تا ۱۴ هستم»"""
    WEEKDAYS = [
        (0, "شنبه"),
        (1, "یک‌شنبه"),
        (2, "دوشنبه"),
        (3, "سه‌شنبه"),
        (4, "چهارشنبه"),
        (5, "پنج‌شنبه"),
        (6, "جمعه"),
    ]

    consultant = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="weekly_schedules", verbose_name="مشاور",
    )
    weekday = models.IntegerField("روز هفته", choices=WEEKDAYS)
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "برنامهٔ هفتگی"
        verbose_name_plural = "برنامه‌های هفتگی"
        unique_together = [("consultant", "weekday")]
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.consultant.get_full_name()} — {self.get_weekday_display()}"


# ==================================================
# استثناهای برنامه (مرخصی، ساعت ویژه، تعطیلی)
# ==================================================

class ConsultantScheduleOverride(models.Model):
    """
    استثنا روی برنامهٔ هفتگی.
    سه حالت:
      1) تعطیلی کامل: is_off=True
      2) ساعت ویژه: custom_start/custom_end
      3) تعطیلی یک بازه از تاریخ
    """
    consultant = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="schedule_overrides", verbose_name="مشاور",
    )
    from_date = models.DateField("از تاریخ", db_index=True)
    to_date = models.DateField("تا تاریخ", db_index=True)

    is_off = models.BooleanField(
        "تعطیل کامل", default=False,
        help_text="اگر بله، این بازه کاملاً تعطیل است",
    )
    custom_start = models.TimeField("ساعت شروع ویژه", null=True, blank=True)
    custom_end = models.TimeField("ساعت پایان ویژه", null=True, blank=True)

    apply_to_all_weekdays = models.BooleanField(
        "اعمال روی همهٔ روزهای هفته", default=True,
    )

    reason = models.CharField("دلیل", max_length=200, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="overrides_created", verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "استثنای برنامه"
        verbose_name_plural = "استثناهای برنامه"
        ordering = ["-from_date"]
        indexes = [
            models.Index(fields=["consultant", "from_date", "to_date"]),
        ]

    def __str__(self):
        if self.is_off:
            return f"{self.consultant.get_full_name()} — تعطیل {self.from_date} تا {self.to_date}"
        return f"{self.consultant.get_full_name()} — ساعت ویژه {self.from_date}"


# ==================================================
# تنظیمات اسلات‌بندی نوبت
# ==================================================

class ConsultantSlotSettings(models.Model):
    """تنظیمات اسلات‌بندی نوبت — مثلاً «هر ۵۰ دقیقه یک نوبت»"""
    consultant = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="slot_settings", verbose_name="مشاور",
    )
    slot_minutes = models.PositiveIntegerField(
        "طول هر اسلات (دقیقه)", default=50,
    )
    buffer_minutes = models.PositiveIntegerField(
        "فاصلهٔ بین اسلات‌ها (دقیقه)", default=0,
    )
    max_daily_sessions = models.PositiveIntegerField(
        "حداکثر جلسات روزانه", default=8,
    )
    allow_overlap = models.BooleanField(
        "اجازهٔ هم‌پوشانی", default=False,
        help_text="اجازهٔ رزرو هم‌پوشان (مثلاً گروه‌درمانی)",
    )

    class Meta:
        verbose_name = "تنظیمات اسلات"
        verbose_name_plural = "تنظیمات اسلات‌ها"

    def __str__(self):
        return f"اسلات {self.consultant.get_full_name()}: {self.slot_minutes} دقیقه"


# ==================================================
# تاریخچهٔ تغییرات برنامه
# ==================================================

class ScheduleChangeLog(models.Model):
    """تاریخچهٔ کامل تغییرات برنامه — برای شفافیت"""
    CHANGE_TYPES = [
        ("activate", "فعال‌سازی"),
        ("deactivate", "غیرفعال‌سازی"),
        ("time_change", "تغییر ساعت"),
        ("leave", "مرخصی"),
        ("room_change", "تغییر اتاق"),
        ("bulk_update", "به‌روزرسانی گروهی"),
    ]

    consultant = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="schedule_history", verbose_name="مشاور",
    )
    changed_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name="schedule_changes_made", verbose_name="تغییردهنده",
    )

    date = models.DateField("تاریخ تغییر", db_index=True)
    change_type = models.CharField("نوع تغییر", max_length=20, choices=CHANGE_TYPES)

    before = models.JSONField("قبل", default=dict)
    after = models.JSONField("بعد", default=dict)

    reason = models.CharField("دلیل", max_length=300, blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "تغییر برنامه"
        verbose_name_plural = "تغییرات برنامه"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consultant", "-created_at"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.consultant.get_full_name()} — {self.get_change_type_display()} ({self.date})"


# ==================================================
# شیفت منشی
# ==================================================

class SecretaryShift(models.Model):
    """شیفت منشی + بخش مسئولیت"""
    SECTIONS = [
        ("reception", "پذیرش و ارسال به مشاور"),
        ("followup", "پیگیری رزرو و کنسلی"),
        ("finance", "صندوق و پرداخت"),
        ("full", "دسترسی کامل"),
    ]

    secretary = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="shifts", verbose_name="منشی",
    )
    date = models.DateField("تاریخ", db_index=True)
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")
    section = models.CharField(
        "بخش", max_length=20, choices=SECTIONS, default="full",
    )
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "شیفت منشی"
        verbose_name_plural = "شیفت‌های منشی"
        ordering = ["-date", "start_time"]
        indexes = [
            models.Index(fields=["date", "section"]),
            models.Index(fields=["secretary", "-date"]),
        ]

    def __str__(self):
        return f"{self.secretary.get_full_name()} — {self.date} ({self.get_section_display()})"