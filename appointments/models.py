from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class WeeklySchedule(models.Model):
    """برنامه‌ی هفتگی مشاور — نسخهٔ قدیمی (فاز بعد بازنویسی می‌شود)."""

    WEEKDAYS = [
        (0, "شنبه"),
        (1, "یک‌شنبه"),
        (2, "دوشنبه"),
        (3, "سه‌شنبه"),
        (4, "چهارشنبه"),
        (5, "پنج‌شنبه"),
        (6, "جمعه"),
    ]

    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="legacy_weekly_schedules", verbose_name="مشاور",
    )
    day_of_week = models.PositiveSmallIntegerField("روز هفته", choices=WEEKDAYS)
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")
    slot_duration = models.PositiveSmallIntegerField(
        "طول هر نوبت (دقیقه)", default=50,
        help_text="مثال: ۵۰ دقیقه برای مشاوره",
    )
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "برنامه هفتگی (قدیمی)"
        verbose_name_plural = "برنامه‌های هفتگی (قدیمی)"
        ordering = ["physician", "day_of_week", "start_time"]
        unique_together = [("physician", "day_of_week", "start_time")]
        indexes = [
            models.Index(fields=["physician", "day_of_week", "is_active"], name="sched_phys_day_idx"),
        ]

    def __str__(self):
        return f"{self.physician.get_full_name()} — {self.get_day_of_week_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("ساعت شروع باید قبل از ساعت پایان باشد.")


class TimeOff(models.Model):
    """روزهای تعطیل یا مرخصی مشاور."""

    REASONS = [
        ("vacation", "مرخصی"),
        ("holiday", "تعطیل رسمی"),
        ("sick", "مراجعی"),
        ("conference", "همایش / سفر"),
        ("personal", "شخصی"),
        ("other", "سایر"),
    ]

    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="time_offs", verbose_name="مشاور",
    )
    date = models.DateField("تاریخ")
    all_day = models.BooleanField("تمام روز", default=True)
    start_time = models.TimeField("از ساعت", null=True, blank=True)
    end_time = models.TimeField("تا ساعت", null=True, blank=True)
    reason = models.CharField("دلیل", max_length=20, choices=REASONS, default="vacation")
    note = models.TextField("یادداشت", blank=True)

    class Meta:
        verbose_name = "مرخصی / تعطیلی"
        verbose_name_plural = "مرخصی‌ها و تعطیلی‌ها"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["physician", "date"], name="timeoff_phys_date_idx"),
            models.Index(fields=["-date"], name="timeoff_date_idx"),
        ]

    def __str__(self):
        return f"{self.physician.get_full_name()} — {self.date} ({self.get_reason_display()})"


class Appointment(models.Model):
    """یک نوبت مشاوره."""

    STATUS = [
        ("scheduled", "برنامه‌ریزی‌شده"),
        ("confirmed", "تأیید شده"),
        ("arrived", "حاضر شد"),
        ("in_progress", "در حال مشاوره"),
        ("completed", "انجام شد"),
        ("cancelled", "لغو شده"),
        ("no_show", "غیبت"),
    ]

    SOURCE = [
        ("in_person", "حضوری"),
        ("phone", "تلفنی"),
        ("online", "آنلاین"),
    ]

    PAYMENT_STATUS = [
        ("not_required", "نیاز به پرداخت ندارد"),
        ("unpaid", "پرداخت‌نشده"),
        ("pending", "در انتظار تأیید درگاه"),
        ("paid", "پرداخت‌شده"),
        ("refunded", "بازگشت داده شده"),
        ("failed", "ناموفق"),
    ]

    PAYMENT_METHOD = [
        ("cash", "نقدی"),
        ("card", "کارت‌خوان"),
        ("online", "درگاه اینترنتی"),
        ("insurance", "بیمه"),
        ("free", "رایگان"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE,
        related_name="appointments", verbose_name="مراجع",
    )
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="appointments", verbose_name="مشاور",
    )
    date = models.DateField("تاریخ نوبت")
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")
    status = models.CharField("وضعیت", max_length=20, choices=STATUS, default="scheduled")
    source = models.CharField("نحوه‌ی ثبت", max_length=20, choices=SOURCE, default="in_person")
    reason = models.TextField("علت مراجعه", blank=True)
    note = models.TextField("یادداشت", blank=True)

    # ====== تبدیل به جلسه ======
    visit = models.OneToOneField(
        "records.Visit", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="appointment",
        verbose_name="جلسهٔ تبدیل‌شده",
    )

    # ====== پرداخت ======
    payment_status = models.CharField(
        "وضعیت پرداخت", max_length=20,
        choices=PAYMENT_STATUS, default="not_required",
    )
    payment_amount = models.DecimalField(
        "مبلغ (تومان)", max_digits=14, decimal_places=0,
        null=True, blank=True,
    )
    payment_method = models.CharField(
        "روش پرداخت", max_length=20,
        choices=PAYMENT_METHOD, default="cash", blank=True,
    )
    transaction_id = models.CharField(
        "کد رهگیری پرداخت", max_length=100,
        blank=True, default="",
        help_text="کد مرجع درگاه پرداخت (در صورت پرداخت آنلاین)",
    )
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)

    # ====== پیامک ======
    confirmation_sent = models.BooleanField("پیامک تأیید ارسال شد", default=False)
    confirmation_sent_at = models.DateTimeField("زمان ارسال تأیید", null=True, blank=True)
    reminder_sent = models.BooleanField("پیامک یادآوری ارسال شد", default=False)
    reminder_sent_at = models.DateTimeField("زمان یادآوری", null=True, blank=True)
    reminder_response = models.CharField(
        "پاسخ مراجع به یادآوری", max_length=200, blank=True, default="",
        help_text="مثلاً: تأیید شد، لغو شد",
    )

    # ====== متادیتا ======
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="created_appointments", verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["date", "physician"], name="apt_date_phys_idx"),
            models.Index(fields=["date", "start_time"], name="apt_date_time_idx"),
            models.Index(fields=["patient", "-date"], name="apt_patient_idx"),
            models.Index(fields=["status"], name="apt_status_idx"),
            models.Index(fields=["payment_status"], name="apt_payment_idx"),
        ]

    def __str__(self):
        return f"{self.patient.full_name} — {self.date} {self.start_time:%H:%M}"

    def clean(self):
        if self.date and self.start_time and self.end_time and self.physician:
            conflicts = Appointment.objects.filter(
                physician=self.physician,
                date=self.date,
                status__in=["scheduled", "confirmed", "arrived", "in_progress"],
            ).exclude(pk=self.pk).filter(
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if conflicts.exists():
                raise ValidationError("این بازه‌ی زمانی با نوبت دیگری تداخل دارد.")

    @property
    def status_badge(self):
        mapping = {
            "scheduled": ("bg-info text-dark", "برنامه‌ریزی‌شده"),
            "confirmed": ("bg-primary", "تأیید شده"),
            "arrived": ("bg-success", "حاضر شد"),
            "in_progress": ("bg-warning text-dark", "در حال مشاوره"),
            "completed": ("bg-success", "انجام شد"),
            "cancelled": ("bg-secondary", "لغو شده"),
            "no_show": ("bg-danger", "غیبت"),
        }
        return mapping.get(self.status, ("bg-light text-dark", self.get_status_display()))

    @property
    def payment_badge(self):
        mapping = {
            "not_required": ("bg-light text-dark", "—"),
            "unpaid": ("bg-warning text-dark", "پرداخت‌نشده"),
            "pending": ("bg-info text-dark", "در انتظار"),
            "paid": ("bg-success", "پرداخت‌شده"),
            "refunded": ("bg-secondary", "بازگشت داده"),
            "failed": ("bg-danger", "ناموفق"),
        }
        return mapping.get(self.payment_status, ("bg-light text-dark", self.get_payment_status_display()))

    @property
    def is_paid(self):
        return self.payment_status == "paid"

    @property
    def duration_minutes(self):
        from datetime import datetime, date
        d = date.today()
        s = datetime.combine(d, self.start_time)
        e = datetime.combine(d, self.end_time)
        return int((e - s).total_seconds() / 60)

    @property
    def is_today(self):
        from datetime import date
        return self.date == date.today()