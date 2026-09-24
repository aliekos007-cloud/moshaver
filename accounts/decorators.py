"""دکوراتورهای کنترل دسترسی — نسخهٔ مرکز مشاوره."""
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from . import permissions as perms


def _deny(request, message="دسترسی مجاز نیست."):
    """راهکار مشترک برای رد دسترسی"""
    from django.contrib import messages
    messages.error(request, message)
    raise PermissionDenied(message)


# ==================================================
# دکوراتورهای نقش پایه
# ==================================================

def manager_required(view_func):
    """فقط مدیر"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.is_manager(request.user):
            _deny(request, "این بخش فقط برای مدیر مجاز است.")
        return view_func(request, *args, **kwargs)
    return wrapper


def consultant_required(view_func):
    """فقط مشاور"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.is_consultant(request.user):
            _deny(request, "این بخش فقط برای مشاور مجاز است.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== سازگاری با کد قدیمی =====
def physician_required(view_func):
    """alias قدیمی برای consultant_required"""
    return consultant_required(view_func)


def secretary_required(view_func):
    """فقط منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.is_secretary(request.user):
            _deny(request, "این بخش فقط برای منشی مجاز است.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای اطلاعات بالینی
# ==================================================

def medical_view_required(view_func):
    """دیدن اطلاعات بالینی — مشاور و مدیر (نه منشی)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_view_medical(request.user):
            _deny(request, "دسترسی به اطلاعات بالینی مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def medical_edit_required(view_func):
    """ویرایش اطلاعات بالینی — مشاور و مدیر (نه منشی)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_edit_medical(request.user):
            _deny(request, "ویرایش اطلاعات بالینی مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای شرح حال محرمانه
# ==================================================

def narrative_view_required(view_func):
    """دیدن شرح حال — فقط مشاور و مدیر"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_view_narrative(request.user):
            _deny(request, "دسترسی به شرح حال مجاز نیست. (فقط مشاور و مدیر)")
        return view_func(request, *args, **kwargs)
    return wrapper


def narrative_edit_required(view_func):
    """ویرایش شرح حال — فقط مشاور صاحب پرونده و مدیر"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_edit_narrative(request.user):
            _deny(request, "ویرایش شرح حال مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای مالی
# ==================================================

def finance_view_required(view_func):
    """دیدن مالی — مدیر، مشاور، منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_view_finance(request.user):
            _deny(request, "دسترسی به مالی مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def finance_edit_required(view_func):
    """ویرایش مالی — مدیر و منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_edit_finance(request.user):
            _deny(request, "ویرایش مالی مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای نوبت و تایمر
# ==================================================

def appointments_required(view_func):
    """نوبت‌دهی — مدیر، مشاور، منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_manage_appointments(request.user):
            _deny(request, "دسترسی به نوبت‌دهی مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def timer_control_required(view_func):
    """کنترل تایمر جلسه — مدیر و منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_control_timer(request.user):
            _deny(request, "کنترل تایمر فقط برای مدیر و منشی مجاز است.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای حضور و اتاق
# ==================================================

def presence_manage_required(view_func):
    """ثبت حضور مشاور — مدیر و منشی"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_manage_presence(request.user):
            _deny(request, "ثبت حضور فقط برای مدیر و منشی مجاز است.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای مراجعین
# ==================================================

def client_register_required(view_func):
    """ثبت مراجع — همه نقش‌ها"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_quick_register_patient(request.user):
            _deny(request, "ثبت مراجع مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================================================
# دکوراتورهای جلسه
# ==================================================

def session_view_required(view_func):
    """دیدن جلسه"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_view_session(request.user):
            _deny(request, "دسترسی به جلسه مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def session_note_required(view_func):
    """یادداشت جلسه — فقط مشاور و مدیر (نه منشی)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not perms.can_view_session_note(request.user):
            _deny(request, "دسترسی به یادداشت جلسه مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper