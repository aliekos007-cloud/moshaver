"""
مدیریت trial با ۳ لایه ذخیره‌سازی:
۱. دیتابیس
۲. فایل مخفی با امضای HMAC
۳. رجیستری ویندوز
"""
import hashlib
import hmac
import json
import os
import platform
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from .fingerprint import get_machine_fingerprint

TRIAL_DAYS = 14


def _get_secret():
    """کلید مخفی مشتق‌شده."""
    base = settings.SECRET_KEY + "|" + get_machine_fingerprint()
    return hashlib.sha256(base.encode()).hexdigest()


def _sign(data_dict):
    """امضای داده با HMAC."""
    payload = json.dumps(data_dict, sort_keys=True, default=str)
    sig = hmac.new(_get_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig


def _verify(data_dict, signature):
    """بررسی صحت امضا."""
    expected = _sign(data_dict)
    return hmac.compare_digest(expected, signature)


def _file_path():
    """مسیر فایل مخفی."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home()
    path = base / ".moshaver"
    path.mkdir(exist_ok=True)
    return path / "install.json"


# ===== لایه ۱: دیتابیس =====

def _read_from_db():
    from .models import TrialState
    try:
        state = TrialState.objects.first()
        if state:
            return {
                "first_run": state.first_run_date.isoformat(),
                "fingerprint": state.machine_fingerprint,
            }
    except Exception:
        pass
    return None


def _write_to_db(data):
    from .models import TrialState
    from datetime import date as dt
    try:
        state, _ = TrialState.objects.get_or_create(pk=1)
        state.first_run_date = dt.fromisoformat(data["first_run"])
        state.machine_fingerprint = data["fingerprint"]
        state.save()
    except Exception:
        pass


# ===== لایه ۲: فایل مخفی =====

def _read_from_file():
    path = _file_path()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        payload = {
            "first_run": data["first_run"],
            "fingerprint": data["fingerprint"],
        }
        if not _verify(payload, data.get("signature", "")):
            return None  # امضا خرابه = دست‌کاری شده
        return payload
    except Exception:
        return None


def _write_to_file(data):
    path = _file_path()
    payload = {
        "first_run": data["first_run"],
        "fingerprint": data["fingerprint"],
    }
    payload["signature"] = _sign(payload)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


# ===== لایه ۳: رجیستری ویندوز =====

def _read_from_registry():
    if platform.system() != "Windows":
        return None
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Moshaver\Install",
            0, winreg.KEY_READ,
        )
        first_run, _ = winreg.QueryValueEx(key, "FirstRun")
        fingerprint, _ = winreg.QueryValueEx(key, "Fingerprint")
        signature, _ = winreg.QueryValueEx(key, "Signature")
        winreg.CloseKey(key)

        payload = {"first_run": first_run, "fingerprint": fingerprint}
        if not _verify(payload, signature):
            return None
        return payload
    except Exception:
        return None


def _write_to_registry(data):
    if platform.system() != "Windows":
        return
    try:
        import winreg
        key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            r"Software\Moshaver\Install",
            0, winreg.KEY_WRITE,
        )
        payload = {"first_run": data["first_run"], "fingerprint": data["fingerprint"]}
        sig = _sign(payload)
        winreg.SetValueEx(key, "FirstRun", 0, winreg.REG_SZ, payload["first_run"])
        winreg.SetValueEx(key, "Fingerprint", 0, winreg.REG_SZ, payload["fingerprint"])
        winreg.SetValueEx(key, "Signature", 0, winreg.REG_SZ, sig)
        winreg.CloseKey(key)
    except Exception:
        pass


# ===== API عمومی =====

def get_install_state():
    """
    خوندن وضعیت نصب از ۳ منبع.
    اگه اختلاف بود، قدیمی‌ترین تاریخ انتخاب می‌شه (جلوی تقلب رو می‌گیره).
    """
    fp = get_machine_fingerprint()
    sources = []

    for reader, name in [
        (_read_from_db, "db"),
        (_read_from_file, "file"),
        (_read_from_registry, "registry"),
    ]:
        data = reader()
        if data and data.get("fingerprint") == fp:
            sources.append((name, data))

    if not sources:
        return None

    # قدیمی‌ترین تاریخ رو انتخاب کن
    sources.sort(key=lambda s: s[1]["first_run"])
    return sources[0][1]


def initialize_trial():
    """اگه نصب جدید باشه، تاریخ اولین اجرا رو ثبت می‌کنه."""
    existing = get_install_state()
    if existing:
        return existing

    fp = get_machine_fingerprint()
    now = datetime.now().isoformat()
    data = {"first_run": now, "fingerprint": fp}

    _write_to_db(data)
    _write_to_file(data)
    _write_to_registry(data)
    return data


def get_trial_info():
    """اطلاعات trial فعلی."""
    state = get_install_state()
    if not state:
        state = initialize_trial()

    try:
        first_run = datetime.fromisoformat(state["first_run"])
    except Exception:
        first_run = datetime.now()

    first_date = first_run.date()
    today = date.today()
    elapsed = (today - first_date).days
    remaining = max(0, TRIAL_DAYS - elapsed)

    return {
        "first_run": first_date,
        "elapsed_days": elapsed,
        "remaining_days": remaining,
        "total_days": TRIAL_DAYS,
        "is_expired": remaining <= 0,
        "is_active": remaining > 0,
    }


def is_app_usable():
    """آیا سامانه قابل استفاده‌ست؟ (لایسنس معتبر یا trial فعال)"""
    from .models import License
    lic = License.get_current()
    if lic and lic.is_valid:
        return True, "license"
    trial = get_trial_info()
    if trial["is_active"]:
        return True, "trial"
    return False, "expired"