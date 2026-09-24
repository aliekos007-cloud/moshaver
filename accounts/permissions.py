"""توابع کمکی برای بررسی نقش کاربر — نسخهٔ مرکز مشاوره."""


# ==================================================
# نقش‌های پایه
# ==================================================

def is_manager(user):
    """مدیر مرکز — همه دسترسی"""
    return user.is_authenticated and (
        user.is_superuser or getattr(user, "role", None) == "manager"
    )


def is_consultant(user):
    """مشاور — دسترسی به مراجعین خودش"""
    return user.is_authenticated and getattr(user, "role", None) == "consultant"


def is_secretary(user):
    """منشی — نوبت، مالی، تایمر — بدون شرح حال"""
    return user.is_authenticated and getattr(user, "role", None) == "secretary"


# ===== سازگاری با کد قدیمی =====
def is_physician(user):
    """alias قدیمی برای is_consultant — برای سازگاری"""
    return is_consultant(user)


# ==================================================
# اطلاعات بالینی (Clinical)
# ==================================================

def can_view_medical(user):
    """دیدن اطلاعات بالینی — فقط مشاور و مدیر (نه منشی)"""
    return is_manager(user) or is_consultant(user)


def can_edit_medical(user):
    """ویرایش اطلاعات بالینی — فقط مشاور و مدیر"""
    return is_manager(user) or is_consultant(user)


# ==================================================
# شرح حال محرمانه (Narrative)
# ==================================================

def can_view_narrative(user, client=None):
    """
    دیدن شرح حال — فقط مشاور صاحب پرونده و مدیر.
    منشی هیچ دسترسی‌ای ندارد.
    """
    if is_manager(user):
        return True
    if not is_consultant(user):
        return False
    if client is None:
        return True  # فقط چک نقش
    # مشاور فقط مراجعین خودش
    if client.assigned_consultant_id == user.id:
        return True
    # یا مشاوری که قبلاً با این مراجع جلسه داشته
    from records.models import Session
    return Session.objects.filter(client=client, consultant=user).exists()


def can_edit_narrative(user, client=None):
    """ویرایش شرح حال — مشاور صاحب پرونده یا مدیر"""
    if is_manager(user):
        return True
    if not is_consultant(user):
        return False
    if client is None:
        return True
    return client.assigned_consultant_id == user.id


# ==================================================
# مالی (Finance)
# ==================================================

def can_view_finance(user):
    """دیدن مالی — مدیر، مشاور، منشی"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_edit_finance(user):
    """ویرایش مالی — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


def can_manage_pricing(user):
    """مدیریت تعرفه و سطح مشاور — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


def can_register_payment(user):
    """ثبت پرداخت — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# نوبت‌دهی و عملیات
# ==================================================

def can_manage_appointments(user):
    """نوبت‌دهی — مدیر، مشاور، منشی"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_view_appointments(user):
    """دیدن نوبت‌ها"""
    return can_manage_appointments(user)


def can_control_timer(user):
    """کنترل تایمر جلسه (شروع/پایان/Pause) — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


def can_view_dashboard_live(user):
    """داشبورد زندهٔ منشی — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# برنامه‌ریزی مشاور
# ==================================================

def can_edit_own_schedule(user):
    """مشاور بتواند برنامهٔ خودش را تنظیم کند"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_edit_any_schedule(user):
    """ویرایش برنامهٔ دیگران — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


def can_view_any_schedule(user):
    """دیدن برنامهٔ همه — فقط مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# حضور و اتاق
# ==================================================

def can_manage_presence(user):
    """ثبت حضور مشاور — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


def can_change_room(user):
    """تغییر اتاق مشاور — مدیر و منشی"""
    return is_manager(user) or is_secretary(user)


# ==================================================
# مدیریت کاربران و تنظیمات
# ==================================================

def can_manage_users(user):
    """مدیریت کاربران — فقط مدیر"""
    return is_manager(user)


def can_edit_clinic_settings(user):
    """تنظیمات مرکز — مدیر و مشاور"""
    return is_manager(user) or is_consultant(user)


def can_view_audit_log(user):
    """مشاهدهٔ گزارش فعالیت‌ها — فقط مدیر"""
    return is_manager(user)


# ==================================================
# مراجعین (Clients)
# ==================================================

def can_quick_register_patient(user):
    """ثبت سریع مراجع — همه نقش‌ها"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_view_client_list(user):
    """دیدن لیست مراجعین — همه نقش‌ها"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_edit_client_basic(user):
    """ویرایش اطلاعات پایهٔ مراجع — همه (جزئیات بالینی جداگانه)"""
    return is_manager(user) or is_consultant(user) or is_secretary(user)


def can_delete_client(user):
    """حذف مراجع — فقط مدیر"""
    return is_manager(user)


# ==================================================
# جلسات (Sessions)
# ==================================================

def can_view_session(user, session=None):
    """دیدن جلسه — مدیر همه، مشاور جلسات خودش، منشی همه"""
    if is_manager(user) or is_secretary(user):
        return True
    if is_consultant(user):
        if session is None:
            return True
        return session.consultant_id == user.id
    return False


def can_edit_session(user, session=None):
    """ویرایش جلسه — مدیر، مشاور صاحب جلسه"""
    if is_manager(user):
        return True
    if is_consultant(user):
        if session is None:
            return True
        return session.consultant_id == user.id
    return False


def can_view_session_note(user, note=None):
    """دیدن یادداشت جلسه (تحلیل مشاور) — فقط مشاور و مدیر"""
    if is_manager(user):
        return True
    if is_consultant(user):
        if note is None:
            return True
        return note.session.consultant_id == user.id
    return False  # منشی: هرگز


def can_edit_session_note(user, note=None):
    """ویرایش یادداشت جلسه — فقط مشاور صاحب جلسه"""
    if is_manager(user):
        return True
    if is_consultant(user):
        if note is None:
            return True
        return note.session.consultant_id == user.id
    return False