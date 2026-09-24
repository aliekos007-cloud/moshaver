"""افزودن وضعیت لایسنس/trial به همه‌ی قالب‌ها."""
from .services import get_trial_info, is_app_usable


def license_status(request):
    try:
        usable, mode = is_app_usable()
        trial = get_trial_info()
        return {
            "app_usable": usable,
            "app_mode": mode,            # license / trial / expired
            "trial_info": trial,
        }
    except Exception:
        return {
            "app_usable": True,
            "app_mode": "license",
            "trial_info": None,
        }