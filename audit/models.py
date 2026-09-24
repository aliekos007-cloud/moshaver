from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """گزارش تمام فعالیت‌های کاربران در سامانه."""

    ACTION_TYPES = [
        ("create", "ایجاد"),
        ("update", "ویرایش"),
        ("delete", "حذف"),
        ("view", "مشاهده"),
        ("login", "ورود"),
        ("logout", "خروج"),
        ("login_failed", "ورود ناموفق"),
        ("export", "خروجی"),
        ("print", "چاپ"),
        ("backup", "پشتیبان‌گیری"),
        ("restore", "بازیابی"),
        ("other", "سایر"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="کاربر",
    )
    user_display = models.CharField("نام کاربر (در لحظه)", max_length=200, blank=True)
    action = models.CharField("نوع اقدام", max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField("مدل", max_length=100, blank=True)
    object_id = models.CharField("شناسه رکورد", max_length=50, blank=True)
    object_repr = models.CharField("توضیح رکورد", max_length=300, blank=True)
    description = models.TextField("توضیحات", blank=True)
    ip_address = models.GenericIPAddressField("آی‌پی", null=True, blank=True)
    user_agent = models.CharField("مرورگر", max_length=300, blank=True)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "گزارش فعالیت"
        verbose_name_plural = "گزارش فعالیت‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="audit_created_idx"),
            models.Index(fields=["user", "-created_at"], name="audit_user_idx"),
            models.Index(fields=["action"], name="audit_action_idx"),
            models.Index(fields=["model_name"], name="audit_model_idx"),
        ]

    def __str__(self):
        return f"{self.user_display or '—'} — {self.get_action_display()} — {self.created_at:%Y/%m/%d %H:%M}"


def log_action(request, action, obj=None, model_name="", object_id="", description="", object_repr=""):
    """ثبت سریع یک رکورد در Audit Log."""
    user = getattr(request, "user", None)
    if user and not user.is_authenticated:
        user = None

    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")

    user_display = ""
    if user:
        try:
            user_display = user.get_full_name() or user.national_code
        except Exception:
            user_display = str(user)

    if obj is not None:
        if not model_name:
            model_name = obj.__class__.__name__
        if not object_id:
            object_id = str(getattr(obj, "pk", "") or "")
        if not object_repr:
            try:
                object_repr = str(obj)[:300]
            except Exception:
                object_repr = ""

    try:
        return AuditLog.objects.create(
            user=user,
            user_display=user_display,
            action=action,
            model_name=model_name,
            object_id=str(object_id or ""),
            object_repr=object_repr,
            description=description,
            ip_address=ip or None,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"AuditLog error: {e}")
        return None