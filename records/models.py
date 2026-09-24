import math
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from patients.models import Patient
from clinic.models import Room


# ==================================================
# مدل قدیمی — Visit (برای سازگاری با دادهٔ قبلی)
# ==================================================

class Visit(models.Model):
    """مراجعه — مدل قدیمی، در فاز بعد کاملاً جایگزین می‌شود."""
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE,
        related_name="visits", verbose_name="مراجع",
    )
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="مشاور",
    )
    visited_at = models.DateTimeField("تاریخ مراجعه", auto_now_add=True)

    prescription_serial = models.CharField(
        "شماره سریال", max_length=30, unique=True,
        blank=True, editable=False, null=True,
    )

    chief_complaint = models.TextField("علت مراجعه", blank=True)
    history = models.TextField("شرح حال", blank=True)
    brief_history = models.TextField("شرح مختصر", blank=True)
    diagnosis = models.TextField("تشخیص", blank=True)
    treatment_plan = models.TextField("برنامه درمان", blank=True)
    follow_up = models.TextField("نتیجه پیگیری", blank=True)

    class Meta:
        verbose_name = "مراجعه (قدیمی)"
        verbose_name_plural = "مراجعات (قدیمی)"
        ordering = ["-visited_at"]
        indexes = [
            models.Index(fields=["patient", "-visited_at"], name="visit_patient_idx"),
            models.Index(fields=["physician", "-visited_at"], name="visit_physician_idx"),
            models.Index(fields=["-visited_at"], name="visit_date_idx"),
        ]

    def __str__(self):
        return f"{self.patient.full_name} — {self.visited_at:%Y/%m/%d}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.prescription_serial:
            import jdatetime
            today = jdatetime.date.today()
            year = str(today.year)
            count = Visit.objects.filter(
                prescription_serial__startswith=f"V-{year}-"
            ).count() + 1
            serial = f"V-{year}-{count:05d}"
            Visit.objects.filter(pk=self.pk).update(prescription_serial=serial)
            self.prescription_serial = serial


# ==================================================
# Session — هستهٔ جلسه
# ==================================================

def calculate_session_fee(duration_minutes, level_snapshot):
    """
    محاسبهٔ هزینهٔ جلسه بر اساس مدت واقعی و سطح مشاور.

    - تا standard_minutes: مبلغ پایه
    - تا grace_minutes بعد: رایگان
    - بعد از آن: دقیقه‌ای/پله‌ای
    """
    if not level_snapshot or duration_minutes is None:
        return Decimal(0)

    standard = level_snapshot.get("standard_minutes", 45)
    grace = level_snapshot.get("grace_minutes", 5)
    rounding = level_snapshot.get("rounding_minutes", 5)
    base_price = Decimal(str(level_snapshot.get("base_price", 0)))
    overtime_rate = Decimal(str(level_snapshot.get("overtime_per_minute", 0)))

    if duration_minutes <= standard + grace:
        return base_price

    overage = duration_minutes - standard - grace
    if rounding > 0:
        overage = math.ceil(overage / rounding) * rounding

    return base_price + (Decimal(overage) * overtime_rate)


class Session(models.Model):
    """
    جلسهٔ مشاوره — هستهٔ زمان، پول و محرمانگی.
    """

    SESSION_TYPES = [
        ("individual", "فردی"),
        ("couple", "زوج"),
        ("family", "خانواده"),
        ("group", "گروه"),
        ("phone", "تلفنی"),
        ("online", "آنلاین"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "زمان‌بندی‌شده"),
        ("in_progress", "در حال مشاوره"),
        ("paused", "وقفه"),
        ("awaiting_payment", "منتظر پرداخت"),
        ("completed", "تسویه‌شده"),
        ("cancelled", "لغو‌شده"),
        ("no_show", "عدم مراجعه"),
    ]

    PAYMENT_STATUS = [
        ("pending", "منتظر پرداخت"),
        ("paid", "پرداخت‌شده"),
        ("deferred", "نسیه"),
        ("partial", "پرداخت جزئی"),
        ("insurance", "بیمه"),
        ("waived", "بخشیده‌شده"),
    ]

    PAYMENT_METHODS = [
        ("cash", "نقدی"),
        ("card", "کارت‌خوان"),
        ("online", "درگاه اینترنتی"),
        ("insurance", "بیمه"),
        ("wallet", "کیف پول"),
        ("other", "سایر"),
    ]

    # ===== اتصالات =====
    client = models.ForeignKey(
        Patient, on_delete=models.PROTECT,
        related_name="sessions", verbose_name="مراجع",
    )
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="sessions", verbose_name="مشاور",
    )
    room = models.ForeignKey(
        Room, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="sessions", verbose_name="اتاق",
    )
    appointment = models.OneToOneField(
        "appointments.Appointment", null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="session", verbose_name="نوبت",
    )

    # ===== اسنپ‌شات سطح مشاور (مهم برای گزارش‌های تاریخی) =====
    level_snapshot = models.JSONField(
        "اسنپ‌شات سطح", default=dict,
        help_text="مشخصات سطح مشاور در لحظهٔ جلسه — تغییر تعرفه بعداً روی این جلسه اثر ندارد",
    )

    # ===== زمان‌بندی =====
    scheduled_start = models.DateTimeField("شروع برنامه‌ریزی‌شده")
    scheduled_end = models.DateTimeField("پایان برنامه‌ریزی‌شده")

    started_at = models.DateTimeField("شروع واقعی", null=True, blank=True)
    ended_at = models.DateTimeField("پایان واقعی", null=True, blank=True)
    actual_duration_minutes = models.PositiveIntegerField(
        "مدت واقعی (دقیقه)", null=True, blank=True,
    )

    # ===== Pause =====
    pause_started_at = models.DateTimeField("شروع وقفه", null=True, blank=True)
    total_paused_seconds = models.PositiveIntegerField(
        "مجموع وقفه‌ها (ثانیه)", default=0,
    )

    # ===== نوع و توضیحات =====
    session_type = models.CharField(
        "نوع جلسه", max_length=20,
        choices=SESSION_TYPES, default="individual",
    )
    session_number = models.PositiveIntegerField(
        "شمارهٔ جلسه", null=True, blank=True,
        help_text="جلسهٔ چندم از این مراجع",
    )
    extension_reason = models.CharField(
        "دلیل تمدید", max_length=200, blank=True,
    )
    secretary_note = models.CharField(
        "یادداشت منشی", max_length=300, blank=True,
    )

    # ===== مالی =====
    calculated_fee = models.DecimalField(
        "مبلغ محاسبه‌شده", max_digits=12, decimal_places=0,
        null=True, blank=True,
    )
    discount_percent = models.PositiveIntegerField("تخفیف (٪)", default=0)
    final_fee = models.DecimalField(
        "مبلغ نهایی", max_digits=12, decimal_places=0,
        null=True, blank=True,
    )

    payment_status = models.CharField(
        "وضعیت پرداخت", max_length=20,
        choices=PAYMENT_STATUS, default="pending",
    )
    payment_method = models.CharField(
        "روش پرداخت", max_length=20,
        choices=PAYMENT_METHODS, blank=True,
    )
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)
    paid_amount = models.DecimalField(
        "مبلغ پرداخت‌شده", max_digits=12, decimal_places=0, default=0,
    )
    remaining_amount = models.DecimalField(
        "مانده", max_digits=12, decimal_places=0, default=0,
    )
    payment_note = models.CharField(
        "یادداشت پرداخت", max_length=300, blank=True,
    )

    # ===== وضعیت =====
    status = models.CharField(
        "وضعیت", max_length=20,
        choices=STATUS_CHOICES, default="scheduled",
    )

    # ===== متادیتا =====
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sessions_created", verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "جلسه"
        verbose_name_plural = "جلسات"
        ordering = ["-scheduled_start"]
        indexes = [
            models.Index(fields=["client", "-scheduled_start"], name="sess_client_idx"),
            models.Index(fields=["consultant", "-scheduled_start"], name="sess_consultant_idx"),
            models.Index(fields=["status", "-scheduled_start"], name="sess_status_idx"),
            models.Index(fields=["room", "scheduled_start"], name="sess_room_idx"),
            models.Index(fields=["-scheduled_start"], name="sess_date_idx"),
        ]

    def __str__(self):
        return f"{self.client.full_name} — {self.get_session_type_display()} — {self.scheduled_start:%Y/%m/%d %H:%M}"

    # ==================================================
    # متدهای زمان
    # ==================================================

    def start(self, by_user=None):
        """شروع جلسه"""
        if self.status not in ("scheduled", "paused"):
            raise ValueError("جلسه در وضعیت قابل شروع نیست.")
        self.started_at = timezone.now()
        self.status = "in_progress"
        self.pause_started_at = None
        self.save()
        return self

    def pause(self, by_user=None):
        """وقفه در جلسه"""
        if self.status != "in_progress":
            raise ValueError("جلسه در حال اجرا نیست.")
        self.pause_started_at = timezone.now()
        self.status = "paused"
        self.save()
        return self

    def resume(self, by_user=None):
        """ادامهٔ جلسه بعد از وقفه"""
        if self.status != "paused" or not self.pause_started_at:
            raise ValueError("جلسه در وقفه نیست.")
        elapsed = (timezone.now() - self.pause_started_at).total_seconds()
        self.total_paused_seconds += int(elapsed)
        self.pause_started_at = None
        self.status = "in_progress"
        self.save()
        return self

    def end(self, by_user=None, ended_at=None):
        """پایان جلسه و محاسبهٔ هزینه"""
        if self.status not in ("in_progress", "paused"):
            raise ValueError("جلسه در حال اجرا نیست.")

        self.ended_at = ended_at or timezone.now()
        self.actual_duration_minutes = self.effective_duration_minutes()
        self.calculated_fee = calculate_session_fee(
            self.actual_duration_minutes, self.level_snapshot
        )

        if self.discount_percent:
            self.final_fee = self.calculated_fee * (100 - self.discount_percent) / 100
        else:
            self.final_fee = self.calculated_fee

        self.remaining_amount = self.final_fee - (self.paid_amount or 0)
        self.status = "awaiting_payment"
        self.save()
        return self

    def effective_duration_minutes(self):
        """مدت مؤثر = کل زمان - وقفه‌ها"""
        if not self.started_at or not self.ended_at:
            return None
        total_seconds = (self.ended_at - self.started_at).total_seconds()
        total_seconds -= self.total_paused_seconds
        return max(0, int(total_seconds // 60))

    def elapsed_seconds(self):
        """ثانیهٔ سپری‌شده از شروع"""
        if not self.started_at:
            return 0
        now = timezone.now()
        total = (now - self.started_at).total_seconds()
        total -= self.total_paused_seconds
        if self.pause_started_at:
            total -= (now - self.pause_started_at).total_seconds()
        return max(0, int(total))

    def remaining_seconds(self):
        """ثانیهٔ باقی‌مانده تا پایان استاندارد"""
        if not self.started_at:
            return None
        standard = self.level_snapshot.get("standard_minutes", 45) * 60
        return standard - self.elapsed_seconds()

    def is_overtime(self):
        """آیا از زمان استاندارد + ارفاق گذشته؟"""
        r = self.remaining_seconds()
        if r is None:
            return False
        grace = self.level_snapshot.get("grace_minutes", 5) * 60
        return r < -grace

    def current_fee(self):
        """هزینهٔ لحظه‌ای (برای نمایش زنده)"""
        minutes = self.elapsed_seconds() // 60
        return calculate_session_fee(minutes, self.level_snapshot)

    # ==================================================
    # متدهای پرداخت
    # ==================================================

    def register_payment(self, amount, method="cash", by_user=None, note=""):
        """ثبت پرداخت"""
        self.paid_amount = (self.paid_amount or 0) + amount
        self.payment_method = method
        self.payment_note = note
        self.remaining_amount = (self.final_fee or 0) - self.paid_amount
        self.paid_at = timezone.now()

        if self.remaining_amount <= 0:
            self.payment_status = "paid"
            self.status = "completed"
        else:
            self.payment_status = "partial"

        self.save()
        return self

    def defer_payment(self, by_user=None, note=""):
        """نسیه"""
        self.payment_status = "deferred"
        self.payment_note = note
        self.status = "completed"
        self.save()
        return self


# ==================================================
# SessionNote — یادداشت جلسه
# ==================================================

class SessionNote(models.Model):
    """یادداشت جلسه — صوتی و/یا متنی."""

    NOTE_STATUS = [
        ("draft", "پیش‌نویس"),
        ("finalized", "نهایی"),
        ("signed", "امضاشده"),
    ]

    TRANSCRIPT_SOURCES = [
        ("whisper", "Whisper AI"),
        ("manual", "دستی"),
        ("voice_typing", "تایپ صوتی مرورگر"),
        ("vosk", "Vosk"),
    ]

    SEVERITY = [
        ("mild", "خفیف"),
        ("moderate", "متوسط"),
        ("severe", "شدید"),
    ]

    PROGRESS = [
        ("better", "بهتر"),
        ("no_change", "بدون تغییر"),
        ("worse", "بدتر"),
    ]

    session = models.OneToOneField(
        Session, on_delete=models.CASCADE,
        related_name="note", verbose_name="جلسه",
    )

    # ===== محتوای متنی =====
    content = models.TextField("متن تحلیل", blank=True)

    # ===== صوتی =====
    has_audio = models.BooleanField("دارای صوت", default=False)
    audio_file = models.FileField(
        "فایل صوتی", upload_to="session_audio/%Y/%m/", blank=True,
    )
    audio_duration_seconds = models.PositiveIntegerField(
        "مدت صوت (ثانیه)", null=True, blank=True,
    )
    audio_size_bytes = models.PositiveBigIntegerField(
        "حجم صوت (بایت)", null=True, blank=True,
    )
    audio_format = models.CharField(
        "فرمت صوت", max_length=10, blank=True,
    )

    # ===== متن تبدیل‌شده =====
    transcript = models.TextField("متن تبدیل‌شده", blank=True)
    transcript_source = models.CharField(
        "منبع تبدیل", max_length=20,
        choices=TRANSCRIPT_SOURCES, blank=True,
    )
    transcript_edited = models.BooleanField("متن ویرایش شد", default=False)
    transcript_edited_at = models.DateTimeField(
        "زمان ویرایش متن", null=True, blank=True,
    )

    # ===== ساختار SOAP =====
    soap_subjective = models.TextField("S — ذهنی", blank=True)
    soap_objective = models.TextField("O — عینی", blank=True)
    soap_assessment = models.TextField("A — ارزیابی", blank=True)
    soap_plan = models.TextField("P — برنامه", blank=True)

    # ===== تگ‌های سریع =====
    tags = models.JSONField("برچسب‌ها", default=list, blank=True)
    severity = models.CharField(
        "شدت", max_length=20, choices=SEVERITY, blank=True,
    )
    progress = models.CharField(
        "پیشرفت", max_length=20, choices=PROGRESS, blank=True,
    )

    # ===== خلاصهٔ AI (آینده) =====
    ai_summary = models.TextField("خلاصهٔ AI", blank=True)
    ai_key_topics = models.JSONField("موضوعات کلیدی AI", default=list, blank=True)
    ai_sentiment = models.CharField("احساس AI", max_length=20, blank=True)

    # ===== متادیتا =====
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="notes_created", verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    version = models.PositiveIntegerField("نسخه", default=1)
    status = models.CharField(
        "وضعیت", max_length=20,
        choices=NOTE_STATUS, default="draft",
    )
    finalized_at = models.DateTimeField("زمان نهایی‌سازی", null=True, blank=True)

    class Meta:
        verbose_name = "یادداشت جلسه"
        verbose_name_plural = "یادداشت‌های جلسه"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="note_created_idx"),
            models.Index(fields=["status"], name="note_status_idx"),
        ]

    def __str__(self):
        return f"یادداشت — {self.session.client.full_name} ({self.session.scheduled_start:%Y/%m/%d})"

    @property
    def full_text(self):
        """متن کامل — ترجیحاً متن ویرایش‌شده، سپس transcript، سپس content"""
        return self.content or self.transcript or ""

    @property
    def effective_duration_minutes(self):
        """مدت مؤثر مکالمه"""
        if not self.audio_duration_seconds:
            return None
        return self.audio_duration_seconds // 60


# ==================================================
# SessionNoteRevision — نسخه‌بندی یادداشت
# ==================================================

class SessionNoteRevision(models.Model):
    """
    هر بار مشاور متن را تغییر می‌دهد، نسخهٔ قبلی ذخیره می‌شود.
    برای AI: می‌فهمیم مشاور چطور فکر می‌کند.
    """
    note = models.ForeignKey(
        SessionNote, on_delete=models.CASCADE,
        related_name="revisions", verbose_name="یادداشت",
    )
    version = models.PositiveIntegerField("نسخه")

    content = models.TextField("متن", blank=True)
    transcript = models.TextField("متن تبدیل‌شده", blank=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name="تغییردهنده",
    )
    changed_at = models.DateTimeField("زمان تغییر", auto_now_add=True)
    change_reason = models.CharField("دلیل تغییر", max_length=200, blank=True)

    class Meta:
        verbose_name = "نسخهٔ یادداشت"
        verbose_name_plural = "نسخه‌های یادداشت"
        ordering = ["-version"]
        unique_together = [("note", "version")]

    def __str__(self):
        return f"نسخه {self.version} — {self.note}"