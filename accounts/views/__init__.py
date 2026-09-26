"""
پکیج views برای اپ accounts.
"""

from .auth import logout_view
from .dashboard import (
    dashboard,
    secretary_dashboard,
)
from .users import (
    user_list,
    user_create,
    user_edit,
    user_toggle_active,
    user_change_password,
)
from .consultants import (
    consultant_level_list,
    consultant_level_create,
    consultant_level_edit,
    consultant_level_toggle,
    consultant_level_delete,
    consultant_weekly_schedule,
    consultants_schedule_list,
    consultant_exceptions,
    consultant_exception_create,
    consultant_exception_delete,
    consultant_month_schedule,
    api_save_day_schedule,
    api_reset_day_schedule,
    slot_search,
    api_day_slots,
)

__all__ = [
    "logout_view",
    "dashboard",
    "secretary_dashboard",
    "user_list",
    "user_create",
    "user_edit",
    "user_toggle_active",
    "user_change_password",
    "consultant_level_list",
    "consultant_level_create",
    "consultant_level_edit",
    "consultant_level_toggle",
    "consultant_level_delete",
    "consultant_weekly_schedule",
    "consultants_schedule_list",
    "consultant_exceptions",
    "consultant_exception_create",
    "consultant_exception_delete",
    "consultant_month_schedule",
    "api_save_day_schedule",
    "api_reset_day_schedule",
    "slot_search",
    "api_day_slots",
]