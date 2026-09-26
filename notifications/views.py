"""ویوهای اعلان."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import Notification
from .services import get_unread_count, mark_all_as_read


@login_required
@require_GET
def api_list(request):
    """لیست اعلان‌های کاربر — آخرین ۲۰ تا."""
    notifications = Notification.objects.filter(
        recipient=request.user,
    ).order_by("-created_at")[:20]

    data = []
    for n in notifications:
        data.append({
            "id": n.pk,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "link": n.link,
            "is_read": n.is_read,
            "created_at_iso": n.created_at.isoformat(),
            "created_at_relative": _relative_time(n.created_at),
        })

    return JsonResponse({
        "ok": True,
        "unread_count": get_unread_count(request.user),
        "notifications": data,
    })


@login_required
@require_GET
def api_unread_count(request):
    """فقط تعداد نخوانده‌ها."""
    return JsonResponse({
        "ok": True,
        "count": get_unread_count(request.user),
    })


@login_required
@require_POST
def api_mark_read(request, pk):
    """علامت‌گذاری یه اعلان به‌عنوان خوانده."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_read()

    return JsonResponse({
        "ok": True,
        "unread_count": get_unread_count(request.user),
    })


@login_required
@require_POST
def api_mark_all_read(request):
    """علامت‌گذاری همه به‌عنوان خوانده."""
    mark_all_as_read(request.user)

    return JsonResponse({
        "ok": True,
        "unread_count": 0,
    })


@login_required
def notification_list(request):
    """صفحهٔ کامل اعلان‌ها."""
    notifications = Notification.objects.filter(
        recipient=request.user,
    ).order_by("-created_at")[:100]

    return render(request, "notifications/list.html", {
        "notifications": notifications,
    })


# ==================================================
# ابزار
# ==================================================

def _relative_time(dt):
    """زمان نسبی: «۳ دقیقه پیش»."""
    from django.utils import timezone

    now = timezone.now()
    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "همین الان"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} دقیقه پیش"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} ساعت پیش"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} روز پیش"
    else:
        import jdatetime
        j = jdatetime.date.fromgregorian(date=dt.date())
        return j.strftime("%Y/%m/%d")