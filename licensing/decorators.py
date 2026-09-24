"""دکوراتور بررسی فعال بودن ماژول."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import License


def feature_required(feature_name):
    """
    دکوراتور بررسی فعال بودن یک ماژول.

    استفاده:
        @feature_required("inventory")
        def inventory_dashboard(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not License.feature_enabled(feature_name):
                return render(request, "licensing/feature_disabled.html", {
                    "feature_name": feature_name,
                    "feature_title": FEATURE_TITLES.get(feature_name, feature_name),
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


FEATURE_TITLES = {
    "inventory": "انبار",
    "finance": "مالی و صندوق",
    "therapies": "درمان‌های تخصصی",
    "documents": "مدارک و تصاویر",
    "consent": "رضایت‌نامه‌ها",
    "reports": "گزارش‌های مدیریتی",
    "backup": "پشتیبان‌گیری",
    "audit": "گزارش فعالیت‌ها",
    "appointments": "نوبت‌دهی",     # ← این خط جدید
}