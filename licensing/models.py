import hashlib
import uuid
from datetime import date, timedelta

from django.conf import settings
from django.db import models


class License(models.Model):
    """لایسنس نرم‌افزار."""

    TIERS = [
        ("trial", "آزمایشی"),
        ("basic", "پایه"),
        ("pro", "حرفه‌ای"),
        ("enterprise", "سازمانی"),
    ]

    STATUS = [
        ("active", "فعال"),
        ("expired", "منقضی"),
        ("suspended", "معلق"),
        ("not_activated", "فعال‌نشده"),
    ]

    # اطلاعات لایسنس
    license_key = models.CharField("کلید لایسنس", max_length=100, unique=True, blank=True)
    serial_number = models.CharField("شماره سریال", max_length=100, unique=True, blank=True)
    tier = models.CharField("نوع لایسنس", max_length=20, choices=TIERS, default="trial")

    # مالک لایسنس
    licensed_to = models.CharField("صادر شده برای", max_length=200, blank=True)
    licensed_email = models.EmailField("ایمیل", blank=True)
    licensed_phone = models.CharField("تلفن", max_length=30, blank=True)

    # محدودیت‌ها
    max_users = models.PositiveIntegerField("حداکثر کاربران", default=3)
    max_physicians = models.PositiveIntegerField("حداکثر پزشکان", default=1)
    max_branches = models.PositiveIntegerField("حداکثر شعب", default=1)

    # ماژول‌ها
    enable_inventory = models.BooleanField("انبار", default=True)
    enable_finance = models.BooleanField("مالی", default=True)
    enable_therapies = models.BooleanField("درمان‌های تخصصی", default=True)
    enable_documents = models.BooleanField("مدارک", default=True)
    enable_consent = models.BooleanField("رضایت‌نامه", default=True)
    enable_reports = models.BooleanField("گزارش‌ها", default=True)
    enable_backup = models.BooleanField("پشتیبان‌گیری", default=True)
    enable_audit = models.BooleanField("گزارش فعالیت‌ها", default=True)
    enable_appointments = models.BooleanField("نوبت‌دهی", default=True)

    # تاریخ‌ها
    activated_at = models.DateTimeField("تاریخ فعال‌سازی", null=True, blank=True)
    valid_from = models.DateField("شروع اعتبار", null=True, blank=True)
    valid_until = models.DateField("پایان اعتبار", null=True, blank=True)
    last_check = models.DateTimeField("آخرین بررسی", null=True, blank=True)

    # وضعیت
    status = models.CharField("وضعیت", max_length=20, choices=STATUS, default="not_activated")
    is_active = models.BooleanField("فعال", default=False)

    # متادیتا
    version = models.CharField("نسخه نرم‌افزار", max_length=20, default="1.0.0")
    installation_id = models.CharField("شناسه نصب", max_length=64, default="", blank=True)
    notes = models.TextField("یادداشت", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "لایسنس"
        verbose_name_plural = "لایسنس‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.license_key} — {self.licensed_to or '—'} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.installation_id:
            self.installation_id = hashlib.md5(
                str(uuid.getnode()).encode()
            ).hexdigest()[:16].upper()

        super().save(*args, **kwargs)

        if is_new and not self.license_key:
            self.license_key = self._generate_key()
            self.serial_number = self._generate_serial()
            License.objects.filter(pk=self.pk).update(
                license_key=self.license_key,
                serial_number=self.serial_number,
            )

    def _generate_key(self):
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        parts = []
        for _ in range(4):
            part = "".join(random.choices(chars, k=4))
            parts.append(part)
        return f"MSHV-{'-'.join(parts)}"

    def _generate_serial(self):
        import jdatetime
        today = jdatetime.date.today()
        return f"SN-{today.year}-{uuid.uuid4().hex[:8].upper()}"

    @property
    def days_remaining(self):
        if not self.valid_until:
            return None
        delta = (self.valid_until - date.today()).days
        return max(0, delta)

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.status != "active":
            return False
        if self.valid_until and self.valid_until < date.today():
            return False
        return True

    @property
    def is_expiring_soon(self):
        if not self.valid_until:
            return False
        days = (self.valid_until - date.today()).days
        return 0 < days <= 30

    @property
    def status_display_badge(self):
        if not self.is_active:
            return ("bg-secondary", "غیرفعال")
        if self.status == "suspended":
            return ("bg-warning text-dark", "معلق")
        if self.valid_until and self.valid_until < date.today():
            return ("bg-danger", "منقضی")
        if self.is_expiring_soon:
            return ("bg-warning text-dark", "به‌زودی منقضی")
        return ("bg-success", "فعال")

    def check_and_update_status(self):
        if self.valid_until and self.valid_until < date.today():
            if self.status == "active":
                self.status = "expired"
                self.is_active = False
                self.save(update_fields=["status", "is_active"])

    def activate(self, days=365):
        from django.utils import timezone
        self.activated_at = timezone.now()
        self.valid_from = date.today()
        self.valid_until = date.today() + timedelta(days=days)
        self.status = "active"
        self.is_active = True
        self.save()

    def deactivate(self):
        self.is_active = False
        self.status = "suspended"
        self.save()

    @classmethod
    def get_current(cls):
        lic = cls.objects.filter(is_active=True).order_by("-created_at").first()
        if lic:
            lic.check_and_update_status()
        return lic

    @classmethod
    def feature_enabled(cls, feature_name):
        """آیا یک ماژول فعاله؟"""
        from .services import is_app_usable
        usable, _ = is_app_usable()
        if not usable:
            return False

        lic = cls.get_current()
        if lic and lic.is_valid:
            return getattr(lic, f"enable_{feature_name}", True)

        # trial فعال — همه ماژول‌ها باز
        return True


class TrialState(models.Model):
    """وضعیت trial — تاریخ اولین اجرا."""

    first_run_date = models.DateField("تاریخ اولین اجرا")
    machine_fingerprint = models.CharField("شناسه سخت‌افزار", max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "وضعیت Trial"
        verbose_name_plural = "وضعیت Trial"

    def __str__(self):
        return f"Trial از {self.first_run_date}"