"""توابع کمکی برای بررسی نقش کاربر."""


def is_manager(user):
    return user.is_authenticated and (
        user.is_superuser or getattr(user, "role", None) == "manager"
    )


def is_physician(user):
    return user.is_authenticated and getattr(user, "role", None) == "physician"


def is_secretary(user):
    return user.is_authenticated and getattr(user, "role", None) == "secretary"


def can_view_medical(user):
    """آیا کاربر اجازه دیدن اطلاعات پزشکی را دارد؟"""
    return is_manager(user) or is_physician(user)


def can_edit_medical(user):
    """آیا کاربر اجازه ویرایش اطلاعات پزشکی را دارد؟"""
    return is_manager(user) or is_physician(user)


def can_view_finance(user):
    """آیا کاربر اجازه دیدن مالی را دارد؟"""
    return is_manager(user) or is_physician(user) or is_secretary(user)


def can_edit_finance(user):
    """آیا کاربر اجازه ویرایش مالی را دارد؟"""
    return is_manager(user) or is_secretary(user)


def can_manage_users(user):
    """آیا کاربر اجازه مدیریت کاربران را دارد؟"""
    return is_manager(user)


def can_edit_clinic_settings(user):
    """آیا کاربر اجازه ویرایش تنظیمات مطب را دارد؟"""
    return is_manager(user) or is_physician(user)

def can_manage_appointments(user):
    """آیا کاربر می‌تونه نوبت بسازه/ویرایش کنه؟"""
    return is_manager(user) or is_physician(user) or is_secretary(user)


def can_view_appointments(user):
    """آیا کاربر می‌تونه نوبت‌ها رو ببینه؟"""
    return can_manage_appointments(user)


def can_quick_register_patient(user):
    """آیا کاربر می‌تونه بیمار جدید ثبت کنه (نسخه سریع)؟"""
    return is_manager(user) or is_physician(user) or is_secretary(user)


def can_edit_medical(user):
    """آیا کاربر اجازه ویرایش اطلاعات پزشکی را دارد؟"""
    return is_manager(user) or is_physician(user)    