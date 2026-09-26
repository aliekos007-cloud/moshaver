from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    اعلان سیستمی برای کاربران.
    """
    TYPE_CHOICES = [
        ("schedule_changed", "تغییر برنامه"),
        ("leave_request", "مرخصی / استثنا"),
        ("new_session", "جلسهٔ جدید"),
        ("session_overdue", "جلسهٔ طولانی"),
        ("payment_deferred", "نسیه"),
        ("survey_response", "نظر مراجع"),
        ("system_alert", "هشدار سیستم"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="گیرنده",
    )

    type = models.CharField("نوع", max_length=30, choices=TYPE_CHOICES)
    title = models.CharField("عنوان", max_length=200)
    message = models.TextField("متن", blank=True)

    # لینک به صفحهٔ مرتبط (اختیاری)
    link = models.CharField("لینک", max_length=500, blank=True)

    # متادیتای اضافی
    payload = models.JSONField("متادیتا", default=dict, blank=True)

    # دیده شده یا نه
    is_read = models.BooleanField("خوانده شده", default=False)
    read_at = models.DateTimeField("زمان خواندن", null=True, blank=True)

    created_at = models.DateTimeField("زمان ساخت", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient.get_full_name()} — {self.title}"

    def mark_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])