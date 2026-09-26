"""داشبوردها — مدیر، منشی، مشاور."""
from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone

from ..models import Role


# ==================================================
# داشبورد اصلی — بر اساس نقش
# ==================================================

@login_required
def dashboard(request):
    """راهنمای ورود — بر اساس نقش، به داشبورد مناسب هدایت می‌کند."""
    role = getattr(request.user, "role", None)

    if role == Role.MANAGER:
        return _manager_dashboard(request)
    if role == Role.SECRETARY:
        return _secretary_dashboard_redirect(request)
    if role == Role.CONSULTANT:
        return _consultant_dashboard(request)

    return _manager_dashboard(request)


def _secretary_dashboard_redirect(request):
    return redirect("secretary_dashboard")


def _manager_dashboard(request):
    """داشبورد مدیر — آمار کلی."""
    from patients.models import Patient
    from records.models import Visit, Session
    from finance.models import Transaction

    today = timezone.localdate()

    patient_count = Patient.objects.count()
    today_visits = Visit.objects.filter(visited_at__date=today).count()
    total_visits = Visit.objects.count()

    today_sessions = Session.objects.filter(scheduled_start__date=today).count()
    active_sessions = Session.objects.filter(status="in_progress").count()

    today_income = Transaction.objects.filter(
        transaction_date=today, transaction_type="income"
    ).aggregate(s=Sum("amount"))["s"] or Decimal(0)
    today_expense = Transaction.objects.filter(
        transaction_date=today, transaction_type="expense"
    ).aggregate(s=Sum("amount"))["s"] or Decimal(0)

    recent_patients = Patient.objects.all()[:5]
    recent_visits = Visit.objects.select_related("patient", "physician")[:5]

    return render(request, "dashboard.html", {
        "patient_count": patient_count,
        "today_visits": today_visits,
        "total_visits": total_visits,
        "today_sessions": today_sessions,
        "active_sessions": active_sessions,
        "today_income": today_income,
        "today_expense": today_expense,
        "recent_patients": recent_patients,
        "recent_visits": recent_visits,
    })


def _consultant_dashboard(request):
    """داشبورد مشاور — جلسات خودش."""
    from records.models import Session

    today = timezone.localdate()

    my_sessions_today = Session.objects.filter(
        consultant=request.user,
        scheduled_start__date=today,
    ).select_related("client", "room").order_by("scheduled_start")

    my_active = Session.objects.filter(
        consultant=request.user,
        status="in_progress",
    ).first()

    my_recent = Session.objects.filter(
        consultant=request.user,
        status="completed",
    ).order_by("-scheduled_start")[:5]

    return render(request, "dashboard_consultant.html", {
        "my_sessions_today": my_sessions_today,
        "my_active": my_active,
        "my_recent": my_recent,
        "today": today,
    })


# ==================================================
# داشبورد عملیاتی منشی
# ==================================================

@login_required
def secretary_dashboard(request):
    """داشبورد زندهٔ منشی — تایم‌لاین عملیاتی."""
    if request.user.role not in (Role.MANAGER, Role.SECRETARY):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from clinic.models import Room
    from records.models import Session
    from accounts.models import Role as R
    from audit.models import AuditLog

    today = timezone.localdate()

    # ===== جلسات امروز =====
    all_sessions_today = Session.objects.filter(
        scheduled_start__date=today,
    ).select_related("client", "consultant", "room").order_by("scheduled_start")

    active_sessions = all_sessions_today.filter(status="in_progress")
    paused_sessions = all_sessions_today.filter(status="paused")
    awaiting_payment = all_sessions_today.filter(status="awaiting_payment")
    scheduled_sessions = all_sessions_today.filter(status="scheduled")
    completed_sessions = all_sessions_today.filter(status="completed")

    # ===== ✅ مشاوران حاضر: از جلسات فعال امروز =====
    present_consultants = []
    seen_ids = set()

    for s in active_sessions:
        if s.consultant_id in seen_ids:
            continue
        seen_ids.add(s.consultant_id)
        present_consultants.append({
            "consultant": s.consultant,
            "room": s.room,
            "status": "in_session",
            "session_id": s.pk,
        })

    # مشاورانی که جلسهٔ بعدی‌شون امروزه (در انتظار)
    for s in scheduled_sessions:
        if s.consultant_id in seen_ids:
            continue
        seen_ids.add(s.consultant_id)
        present_consultants.append({
            "consultant": s.consultant,
            "room": s.room,
            "status": "present",
            "session_id": s.pk,
        })

    # ===== اتاق‌ها =====
    rooms = Room.objects.filter(is_active=True).order_by("order", "name")

    # ===== درآمد امروز =====
    today_income = Session.objects.filter(
        scheduled_start__date=today,
        payment_status="paid",
    ).aggregate(s=Sum("paid_amount"))["s"] or Decimal(0)

    # ===== جلسات ثبت‌شده توسط مشاوران در ۲۴ ساعت اخیر =====
    recent_24h = timezone.now() - timedelta(hours=24)

    recent_consultant_sessions = Session.objects.filter(
        created_at__gte=recent_24h,
        created_by__role=R.CONSULTANT,
        status__in=["scheduled", "in_progress", "paused"],
    ).select_related("client", "consultant", "room").order_by("-created_at")[:10]

    # ===== تغییرات اخیر برنامهٔ مشاوران =====
    recent_schedule_changes = AuditLog.objects.filter(
        action="consultant_schedule_change",
        created_at__gte=recent_24h,
    ).select_related("user").order_by("-created_at")[:5]

    context = {
        "today": today,
        "active_sessions": active_sessions,
        "paused_sessions": paused_sessions,
        "awaiting_payment": awaiting_payment,
        "scheduled_sessions": scheduled_sessions,
        "completed_sessions": completed_sessions,
        "present_consultants": present_consultants,
        "rooms": rooms,
        "today_income": today_income,
        "recent_consultant_sessions": recent_consultant_sessions,
        "recent_schedule_changes": recent_schedule_changes,
        "stats": {
            "active_count": active_sessions.count(),
            "present_count": len(present_consultants),
            "upcoming_count": scheduled_sessions.count(),
            "completed_count": completed_sessions.count(),
        },
    }
    return render(request, "dashboard_secretary.html", context)