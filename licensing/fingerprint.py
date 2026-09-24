"""شناسه سخت‌افزاری برای قفل کردن trial به این نصب."""
import hashlib
import platform
import uuid


def get_machine_fingerprint():
    """یک شناسه‌ی یکتا از سخت‌افزار سیستم."""
    parts = [
        str(uuid.getnode()),        # MAC address
        platform.node(),            # Machine name
        platform.machine(),         # x86_64
        platform.system(),          # Windows
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()