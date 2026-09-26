"""
سرویس‌های اعلان.
"""
from django.conf import settings
from .models import Notification


def notify(recipient, notif_type, title, message="", link="", payload=None):
    """
    ساخت یه اعلان.

    Args:
        recipient: User یا لیست User
        notif_type: نوع اعلان (باید از TYPE_CHOICES باشه)
        title: عنوان
        message: متن
        link: لینک (اختیاری)
        payload: دیکشنری متادیتا (اختیاری)
    """
    if recipient is None:
        return None

    # اگه لیست بود
    if isinstance(recipient, (list, tuple)):
        notifications = []
        for r in recipient:
            n = Notification.objects.create(
                recipient=r,
                type=notif_type,
                title=title,
                message=message,
                link=link,
                payload=payload or {},
            )
            notifications.append(n)
        return notifications

    # تک کاربر
    return Notification.objects.create(
        recipient=recipient,
        type=notif_type,
        title=title,
        message=message,
        link=link,
        payload=payload or {},
    )


def notify_secretaries_and_managers(notif_type, title, message="", link="", payload=None, exclude_user=None):
    """
    اعلان به همهٔ منشی‌ها و مدیران.
    """
    from accounts.models import User, Role

    recipients = User.objects.filter(
        role__in=[Role.MANAGER, Role.SECRETARY],
        is_active=True,
    )

    if exclude_user:
        recipients = recipients.exclude(pk=exclude_user.pk)

    return notify(
        recipient=list(recipients),
        notif_type=notif_type,
        title=title,
        message=message,
        link=link,
        payload=payload,
    )


def get_unread_count(user):
    """تعداد اعلان‌های نخوانده."""
    return Notification.objects.filter(recipient=user, is_read=False).count()


def mark_all_as_read(user):
    """علامت‌گذاری همهٔ اعلان‌ها به‌عنوان خوانده‌شده."""
    from django.utils import timezone
    return Notification.objects.filter(
        recipient=user, is_read=False
    ).update(is_read=True, read_at=timezone.now())