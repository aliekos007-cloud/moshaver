"""دکوراتورهای محدودکننده دسترسی برای viewها."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from . import permissions


def manager_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.is_manager(request.user):
            raise PermissionDenied("شما به این بخش دسترسی ندارید.")
        return view_func(request, *args, **kwargs)
    return wrapper


def physician_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_view_medical(request.user):
            raise PermissionDenied("این بخش فقط برای طبیب و مدیر مطب قابل دسترسی است.")
        return view_func(request, *args, **kwargs)
    return wrapper


def medical_view_required(view_func):
    """اجازه دیدن اطلاعات پزشکی"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_view_medical(request.user):
            raise PermissionDenied("دسترسی به اطلاعات پزشکی برای نقش شما مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def medical_edit_required(view_func):
    """اجازه ویرایش اطلاعات پزشکی"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_edit_medical(request.user):
            raise PermissionDenied("ویرایش اطلاعات پزشکی برای نقش شما مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def finance_view_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_view_finance(request.user):
            raise PermissionDenied("دسترسی به بخش مالی برای نقش شما مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper


def finance_edit_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_edit_finance(request.user):
            raise PermissionDenied("ویرایش مالی برای نقش شما مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper

def appointments_required(view_func):
    """اجازه دسترسی به نوبت‌ها — برای همه نقش‌ها."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not permissions.can_manage_appointments(request.user):
            raise PermissionDenied("دسترسی به نوبت‌ها برای نقش شما مجاز نیست.")
        return view_func(request, *args, **kwargs)
    return wrapper