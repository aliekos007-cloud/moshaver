"""ثبت خودکار ورود/خروج کاربران."""
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed,
)
from django.dispatch import receiver
from .models import AuditLog


def _get_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    try:
        AuditLog.objects.create(
            user=user,
            user_display=user.get_full_name() or user.national_code,
            action="login",
            description="ورود به سامانه",
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception:
        pass


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if not user:
        return
    try:
        AuditLog.objects.create(
            user=user,
            user_display=user.get_full_name() or user.national_code,
            action="logout",
            description="خروج از سامانه",
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception:
        pass


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    if request is None:
        return
    try:
        national_code = credentials.get("username", "ناشناس")
        AuditLog.objects.create(
            user=None,
            user_display=f"تلاش با کد ملی: {national_code}",
            action="login_failed",
            description="ورود ناموفق",
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception:
        pass