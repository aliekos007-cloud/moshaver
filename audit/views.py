from licensing.decorators import feature_required
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from accounts import permissions
from .models import AuditLog

@feature_required("audit")
@login_required
def audit_list(request):
    if not permissions.is_manager(request.user):
        raise PermissionDenied("دسترسی به گزارش فعالیت‌ها فقط برای مدیر مطب مجاز است.")

    qs = AuditLog.objects.select_related("user").all()

    # فیلترها
    action = request.GET.get("action", "")
    user_id = request.GET.get("user", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    q = request.GET.get("q", "").strip()

    if action:
        qs = qs.filter(action=action)
    if user_id:
        qs = qs.filter(user_id=user_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if q:
        qs = qs.filter(
            Q(user_display__icontains=q)
            | Q(description__icontains=q)
            | Q(object_repr__icontains=q)
            | Q(model_name__icontains=q)
            | Q(ip_address__icontains=q)
        )

    # محدود به ۵۰۰ رکورد آخر برای performance
    total = qs.count()
    qs = qs[:500]

    from accounts.models import User
    users = User.objects.filter(is_active=True).order_by("first_name", "last_name")

    return render(request, "audit/list.html", {
        "logs": qs,
        "total": total,
        "users": users,
        "actions": AuditLog.ACTION_TYPES,
        "action_filter": action,
        "user_filter": user_id,
        "from_filter": date_from,
        "to_filter": date_to,
        "q": q,
    })