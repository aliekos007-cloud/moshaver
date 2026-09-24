"""تگ‌های قالبی برای بررسی نقش کاربر در HTML — نسخهٔ مرکز مشاوره."""
from django import template

register = template.Library()


# ==================================================
# نقش‌های پایه
# ==================================================

@register.filter
def is_manager(user):
    """مدیر مرکز"""
    return user.is_authenticated and (
        user.is_superuser or getattr(user, "role", None) == "manager"
    )


@register.filter
def is_consultant(user):
    """مشاور"""
    return user.is_authenticated and getattr(user, "role", None) == "consultant"


@register.filter
def is_physician(user):
    """alias قدیمی برای is_consultant"""
    return is_consultant(user)


@register.filter
def is_secretary(user):
    """منشی"""
    return user.is_authenticated and getattr(user, "role", None) == "secretary"


# ==================================================
# اطلاعات بالینی
# ==================================================

@register.filter
def can_view_medical(user):
    return is_manager(user) or is_consultant(user)


@register.filter
def can_edit_medical(user):
    return is_manager(user) or is_consultant(user)


# ==================================================
# شرح حال محرمانه
# ==================================================

@register.filter
def can_view_narrative(user):
    """دیدن شرح حال — فقط مشاور و مدیر"""
    return is_manager(user) or is_consultant(user)


@register.filter
def can_edit_narrative(user):
    """ویرایش شرح حال — فقط مشاور و مدیر"""
    return is_manager(user) or is_consultant(user)


# ==================================================
# مالی
# ==================================================

@register.filter
def can_view_finance(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_edit_finance(user):
    return is_manager(user) or is_secretary(user)


@register.filter
def can_manage_pricing(user):
    """مدیریت تعرفه و سطح مشاور"""
    return is_manager(user) or is_secretary(user)


@register.filter
def can_register_payment(user):
    """ثبت پرداخت"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# نوبت و تایمر
# ==================================================

@register.filter
def can_manage_appointments(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_control_timer(user):
    """کنترل تایمر جلسه — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


@register.filter
def can_view_dashboard_live(user):
    """داشبورد زنده — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# برنامه‌ریزی
# ==================================================

@register.filter
def can_edit_own_schedule(user):
    """تنظیم برنامهٔ خودش"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_edit_any_schedule(user):
    """ویرایش برنامهٔ دیگران — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


@register.filter
def can_view_any_schedule(user):
    """دیدن برنامهٔ همه — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# حضور و اتاق
# ==================================================

@register.filter
def can_manage_presence(user):
    """ثبت حضور مشاور"""
    return is_manager(user) or is_secretary(user)


@register.filter
def can_change_room(user):
    """تغییر اتاق"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# کاربران و تنظیمات
# ==================================================

@register.filter
def can_manage_users(user):
    return is_manager(user)


@register.filter
def can_edit_clinic_settings(user):
    return is_manager(user) or is_consultant(user)


@register.filter
def can_view_audit_log(user):
    return is_manager(user)


# ==================================================
# مراجعین
# ==================================================

@register.filter
def can_quick_register_patient(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_view_client_list(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_edit_client_basic(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_delete_client(user):
    return is_manager(user)


# ==================================================
# جلسات
# ==================================================

@register.filter
def can_view_session(user):
    return is_manager(user) or is_consultant(user) or is_secretary(user)


@register.filter
def can_view_session_note(user):
    """دیدن یادداشت جلسه — فقط مشاور و مدیر (نه منشی)"""
    return is_manager(user) or is_consultant(user)


@register.filter
def can_edit_session_note(user):
    """ویرایش یادداشت جلسه — فقط مشاور و مدیر"""
    return is_manager(user) or is_consultant(user)