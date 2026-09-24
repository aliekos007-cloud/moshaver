from django.conf import settings
from django.db import models


class BackupRecord(models.Model):
    STATUS = [
        ("success", "موفق"),
        ("failed", "ناموفق"),
    ]

    file_name = models.CharField("نام فایل", max_length=200)
    file_size = models.BigIntegerField("حجم (بایت)", default=0)
    created_at = models.DateTimeField("تاریخ ساخت", auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name="سازنده",
    )
    status = models.CharField("وضعیت", max_length=10, choices=STATUS, default="success")
    note = models.TextField("یادداشت", blank=True)

    class Meta:
        verbose_name = "پشتیبان"
        verbose_name_plural = "پشتیبان‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name} — {self.created_at:%Y/%m/%d}"

    @property
    def size_display(self):
        size = self.file_size
        if size < 1024:
            return f"{size} بایت"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} کیلوبایت"
        return f"{size / (1024 * 1024):.2f} مگابایت"