"""پکیج views مشاوران — همه توابع رو re-export می‌کنه.

این فایل باعث می‌شه که importهای قبلی مثل:
    from accounts.views import consultant_level_list
هنوز کار کنن، بدون هیچ تغییر در urls.py.
"""
from .levels import (
    consultant_level_list,
    consultant_level_create,
    consultant_level_edit,
    consultant_level_toggle,
    consultant_level_delete,
)
from .schedule import (
    consultants_schedule_list,
    consultant_weekly_schedule,
    consultant_month_schedule,
)
from .exceptions import (
    consultant_exceptions,
    consultant_exception_create,
    consultant_exception_delete,
)
from .api import (
    api_save_day_schedule,
    api_reset_day_schedule,
)
from .search import (
    slot_search,
    api_day_slots,
)

__all__ = [
    "consultant_level_list",
    "consultant_level_create",
    "consultant_level_edit",
    "consultant_level_toggle",
    "consultant_level_delete",
    "consultants_schedule_list",
    "consultant_weekly_schedule",
    "consultant_month_schedule",
    "consultant_exceptions",
    "consultant_exception_create",
    "consultant_exception_delete",
    "api_save_day_schedule",
    "api_reset_day_schedule",
    "slot_search",
    "api_day_slots",
]