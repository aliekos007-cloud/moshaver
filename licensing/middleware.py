"""Middleware قفل کردن سامانه وقتی نه لایسنس داره نه trial."""
from django.shortcuts import render
from .services import is_app_usable, get_trial_info

# مسیرهای همیشه آزاد
EXEMPT_PREFIXES = [
    "/accounts/login/",
    "/accounts/logout/",
    "/licensing/",
    "/admin/",
    "/static/",
    "/media/",
]


class LicenseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # مسیرهای آزاد
        path = request.path
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)

        # سوپریوزر همیشه آزاد
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # بررسی وضعیت
        try:
            usable, mode = is_app_usable()
        except Exception:
            # اگه خطایی رخ داد، اجازه بده رد بشه (fail-safe برای جلوگیری از قفل کامل)
            return self.get_response(request)

        if not usable:
            trial = get_trial_info()
            return render(request, "licensing/expired.html", {
                "trial": trial,
            }, status=403)

        return self.get_response(request)