"""تگ‌های قالبی برای بررسی نقش کاربر در HTML."""
from django import template

register = template.Library()


@register.filter
def is_manager(user):
    return user.is_authenticated and (
        user.is_superuser or getattr(user, "role", None) == "manager"
    )


@register.filter
def is_physician(user):
    return user.is_authenticated and getattr(user, "role", None) == "physician"


@register.filter
def is_secretary(user):
    return user.is_authenticated and getattr(user, "role", None) == "secretary"


@register.filter
def can_view_medical(user):
    return is_manager(user) or is_physician(user)


@register.filter
def can_edit_medical(user):
    return is_manager(user) or is_physician(user)


@register.filter
def can_view_finance(user):
    return is_manager(user) or is_physician(user) or is_secretary(user)


@register.filter
def can_edit_finance(user):
    return is_manager(user) or is_secretary(user)


@register.filter
def can_manage_users(user):
    return is_manager(user)


@register.filter
def can_edit_clinic_settings(user):
    return is_manager(user) or is_physician(user)


@register.filter
def can_manage_appointments(user):
    return is_manager(user) or is_physician(user) or is_secretary(user)


@register.filter
def can_quick_register_patient(user):
    return is_manager(user) or is_physician(user) or is_secretary(user)