from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from audit.models import log_action
from .decorators import manager_required
from .forms import (
    UserCreateForm, UserEditForm, UserPasswordForm,
    ConsultantLevelForm,
)
from .models import User, Role, ConsultantLevel


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
    })


# ==================================================
# داشبورد عملیاتی منشی
# ==================================================

@login_required
def secretary_dashboard(request):
    if request.user.role not in (Role.MANAGER, Role.SECRETARY):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from clinic.models import Room, ConsultantDailyPresence
    from records.models import Session
    from appointments.models import Appointment

    today = timezone.localdate()

    all_sessions_today = Session.objects.filter(
        scheduled_start__date=today,
    ).select_related("client", "consultant", "room").order_by("scheduled_start")

    active_sessions = all_sessions_today.filter(status="in_progress")
    paused_sessions = all_sessions_today.filter(status="paused")
    awaiting_payment = all_sessions_today.filter(status="awaiting_payment")
    scheduled_sessions = all_sessions_today.filter(status="scheduled")
    completed_sessions = all_sessions_today.filter(status="completed")

    present_consultants = ConsultantDailyPresence.objects.filter(
        date=today,
        status__in=["present", "in_session", "on_break"],
    ).select_related("consultant", "room")

    rooms = Room.objects.filter(is_active=True).order_by("order", "name")

    upcoming_appointments = Appointment.objects.filter(
        date=today,
        status__in=["scheduled", "confirmed"],
    ).select_related("patient", "physician").order_by("start_time")

    today_income = Session.objects.filter(
        scheduled_start__date=today,
        payment_status="paid",
    ).aggregate(s=Sum("paid_amount"))["s"] or Decimal(0)

    context = {
        "today": today,
        "active_sessions": active_sessions,
        "paused_sessions": paused_sessions,
        "awaiting_payment": awaiting_payment,
        "scheduled_sessions": scheduled_sessions,
        "completed_sessions": completed_sessions,
        "present_consultants": present_consultants,
        "rooms": rooms,
        "upcoming_appointments": upcoming_appointments,
        "today_income": today_income,
        "stats": {
            "active_count": active_sessions.count(),
            "present_count": present_consultants.count(),
            "upcoming_count": upcoming_appointments.count(),
            "completed_count": completed_sessions.count(),
        },
    }
    return render(request, "dashboard_secretary.html", context)


# ==================================================
# خروج
# ==================================================

def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ==================================================
# مدیریت کاربران
# ==================================================

@manager_required
def user_list(request):
    users = User.objects.all().order_by("-is_active", "last_name", "first_name")
    return render(request, "accounts/user_list.html", {"users": users})


@manager_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(
                request, "create", user,
                description=f"ساخت کاربر جدید: {user.get_full_name()} ({user.get_role_display()})",
            )
            messages.success(request, f"کاربر «{user.get_full_name()}» با موفقیت ساخته شد.")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "کاربر جدید",
    })


@manager_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    is_self = (user.pk == request.user.pk)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            obj = form.save(commit=False)
            if is_self:
                obj.role = user.role
                obj.is_active = True
            obj.save()
            log_action(
                request, "update", user,
                description=f"ویرایش کاربر: {user.get_full_name()}",
            )
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": f"ویرایش {user.get_full_name()}",
        "edit_user": user,
        "is_self": is_self,
    })


@manager_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if user.pk == request.user.pk:
            messages.error(request, "نمی‌توانید حساب خودتان را غیرفعال کنید.")
        else:
            user.is_active = not user.is_active
            user.save()
            status = "فعال" if user.is_active else "غیرفعال"
            log_action(
                request, "update", user,
                description=f"تغییر وضعیت کاربر: {user.get_full_name()} → {status}",
            )
            messages.success(request, f"کاربر {user.get_full_name()} {status} شد.")
    return redirect("user_list")


@manager_required
def user_change_password(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.save()
            log_action(
                request, "update", user,
                description=f"تغییر رمز عبور کاربر: {user.get_full_name()}",
            )
            messages.success(request, f"رمز عبور {user.get_full_name()} با موفقیت تغییر کرد.")
            return redirect("user_list")
    else:
        form = UserPasswordForm()

    return render(request, "accounts/user_password.html", {
        "form": form,
        "edit_user": user,
    })


# ==================================================
# مدیریت سطوح مشاور (ConsultantLevel)
# ==================================================

def _can_manage_levels(user):
    return user.is_authenticated and user.role in ("manager", "secretary")


def consultant_level_list(request):
    """لیست سطوح مشاور — با تعرفه‌ها."""
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    today = timezone.localdate()
    levels = ConsultantLevel.objects.all().order_by("order", "name")

    # شمارش مشاوران هر سطح
    levels_data = []
    for level in levels:
        consultant_count = User.objects.filter(
            consultant_level=level,
            role=Role.CONSULTANT,
            is_active=True,
        ).count()
        levels_data.append({
            "level": level,
            "consultant_count": consultant_count,
        })

    return render(request, "accounts/consultant_level_list.html", {
        "levels_data": levels_data,
        "total": len(levels_data),
    })


def consultant_level_create(request):
    """ساخت سطح مشاور جدید."""
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    if request.method == "POST":
        form = ConsultantLevelForm(request.POST)
        if form.is_valid():
            level = form.save()
            log_action(
                request, "create", level,
                description=f"ساخت سطح مشاور: {level.name}",
            )
            messages.success(request, f"سطح «{level.name}» با موفقیت ساخته شد.")
            return redirect("consultant_level_list")
    else:
        form = ConsultantLevelForm()

    return render(request, "accounts/consultant_level_form.html", {
        "form": form,
        "title": "سطح مشاور جدید",
        "is_edit": False,
    })


def consultant_level_edit(request, pk):
    """ویرایش سطح مشاور."""
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    level = get_object_or_404(ConsultantLevel, pk=pk)

    if request.method == "POST":
        form = ConsultantLevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            log_action(
                request, "update", level,
                description=f"ویرایش سطح مشاور: {level.name}",
            )
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("consultant_level_list")
    else:
        form = ConsultantLevelForm(instance=level)

    return render(request, "accounts/consultant_level_form.html", {
        "form": form,
        "title": f"ویرایش {level.name}",
        "level": level,
        "is_edit": True,
    })


def consultant_level_toggle(request, pk):
    """فعال/غیرفعال کردن سطح."""
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    level = get_object_or_404(ConsultantLevel, pk=pk)

    if request.method == "POST":
        level.is_active = not level.is_active
        level.save()
        status = "فعال" if level.is_active else "غیرفعال"
        log_action(
            request, "update", level,
            description=f"{status} کردن سطح: {level.name}",
        )
        messages.success(request, f"سطح «{level.name}» {status} شد.")
    return redirect("consultant_level_list")


def consultant_level_delete(request, pk):
    """حذف سطح مشاور — فقط اگر مشاوری به آن وصل نباشد."""
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    level = get_object_or_404(ConsultantLevel, pk=pk)

    if request.method == "POST":
        # چک استفاده
        in_use = User.objects.filter(consultant_level=level).exists()

        if in_use:
            messages.error(
                request,
                f"سطح «{level.name}» قابل حذف نیست چون مشاورانی به آن متصل هستند. "
                "می‌توانید آن را غیرفعال کنید."
            )
            return redirect("consultant_level_list")

        name = level.name
        level.delete()
        log_action(request, "delete", None, description=f"حذف سطح مشاور: {name}")
        messages.success(request, f"سطح «{name}» حذف شد.")
        return redirect("consultant_level_list")

    return render(request, "accounts/consultant_level_confirm_delete.html", {"level": level})