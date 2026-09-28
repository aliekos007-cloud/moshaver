"""برنامه هفتگی و ماهانه مشاوران + لیست مشاوران."""
import json
from datetime import timedelta

import jdatetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from ...models import User
from audit.models import log_action
from ._helpers import _notify_schedule_change


def consultants_schedule_list(request):
    """لیست همهٔ مشاوران با خلاصهٔ برنامه هفتگی."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary"):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ...models import ConsultantWeeklySchedule, ConsultantSlotSettings

    consultants = User.objects.filter(
        consultant_level__isnull=False,
    ).order_by("-is_active", "last_name", "first_name")

    weekdays_names = [
        "شنبه", "یک‌شنبه", "دوشنبه",
        "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه",
    ]

    consultants_data = []
    for c in consultants:
        schedules = ConsultantWeeklySchedule.objects.filter(
            consultant=c,
        ).order_by("weekday")

        active_days = []
        for s in schedules:
            if s.is_active:
                active_days.append({
                    "name": weekdays_names[s.weekday],
                    "start": s.start_time.strftime("%H:%M"),
                    "end": s.end_time.strftime("%H:%M"),
                })

        slot_settings = ConsultantSlotSettings.objects.filter(consultant=c).first()

        consultants_data.append({
            "consultant": c,
            "active_days": active_days,
            "active_days_count": len(active_days),
            "has_schedule": len(active_days) > 0,
            "slot_minutes": slot_settings.slot_minutes if slot_settings else 45,
        })

    return render(request, "accounts/consultants_schedule_list.html", {
        "consultants_data": consultants_data,
        "total": len(consultants_data),
    })


def consultant_weekly_schedule(request, pk):
    """نمایش و ویرایش برنامهٔ هفتگی مشاور."""
    if not request.user.is_authenticated:
        return redirect("login")

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    is_manager = role == "manager"
    is_secretary = role == "secretary"
    is_consultant = role == "consultant"

    can_edit = is_manager or is_secretary or (is_self and is_consultant)

    if not can_edit:
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ...models import ConsultantWeeklySchedule, ConsultantSlotSettings
    from records.models import Session

    if request.method == "POST":
        changes_summary = []

        for weekday in range(7):
            active = request.POST.get(f"day_{weekday}_active") == "on"
            start = request.POST.get(f"day_{weekday}_start", "").strip()
            end = request.POST.get(f"day_{weekday}_end", "").strip()
            blocked_raw = request.POST.get(f"day_{weekday}_blocked", "[]")

            try:
                blocked_hours = json.loads(blocked_raw)
                if not isinstance(blocked_hours, list):
                    blocked_hours = []
                blocked_hours = sorted(set(
                    int(h) for h in blocked_hours
                    if 0 <= int(h) <= 23
                ))
            except (json.JSONDecodeError, ValueError, TypeError):
                blocked_hours = []

            old_schedule = ConsultantWeeklySchedule.objects.filter(
                consultant=consultant,
                weekday=weekday,
            ).first()
            old_summary = None
            if old_schedule and old_schedule.is_active:
                old_summary = f"{old_schedule.start_time.strftime('%H:%M')}-{old_schedule.end_time.strftime('%H:%M')}"
                old_blocked = set(old_schedule.blocked_hours or [])
            else:
                old_blocked = set()

            if active and start and end:
                if blocked_hours and old_schedule:
                    today = timezone.localdate()
                    future_sessions = Session.objects.filter(
                        consultant=consultant,
                        status__in=["scheduled"],
                        scheduled_start__date__gte=today,
                        scheduled_start__time__hour__in=blocked_hours,
                    )

                    conflicting = []
                    for s in future_sessions:
                        j_date = jdatetime.date.fromgregorian(date=s.scheduled_start.date())
                        if j_date.weekday() == weekday:
                            conflicting.append(s)

                    if conflicting:
                        messages.warning(
                            request,
                            f"⚠️ {len(conflicting)} نوبت رزرو‌شده در ساعت‌های غیرفعالِ "
                            f"{[f'{h}:00' for h in blocked_hours]} وجود دارد. "
                            "لطفاً نوبت‌ها را بررسی کنید."
                        )

                obj, created = ConsultantWeeklySchedule.objects.update_or_create(
                    consultant=consultant,
                    weekday=weekday,
                    defaults={
                        "start_time": start,
                        "end_time": end,
                        "is_active": True,
                        "blocked_hours": blocked_hours,
                    },
                )

                new_summary = f"{start}-{end}"
                new_blocked = set(blocked_hours)

                if created:
                    changes_summary.append(f"روز {obj.get_weekday_display()} اضافه شد")
                elif old_summary != new_summary or old_blocked != new_blocked:
                    if old_summary != new_summary:
                        changes_summary.append(
                            f"{obj.get_weekday_display()}: {old_summary} → {new_summary}"
                        )
                    if old_blocked != new_blocked:
                        new_blocks = new_blocked - old_blocked
                        removed_blocks = old_blocked - new_blocked
                        if new_blocks:
                            changes_summary.append(
                                f"{obj.get_weekday_display()}: {sorted(new_blocks)} غیرفعال"
                            )
                        if removed_blocks:
                            changes_summary.append(
                                f"{obj.get_weekday_display()}: {sorted(removed_blocks)} فعال"
                            )
            else:
                deleted = ConsultantWeeklySchedule.objects.filter(
                    consultant=consultant,
                    weekday=weekday,
                ).delete()
                if deleted[0] > 0 and old_summary:
                    names = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
                    changes_summary.append(f"{names[weekday]} حذف شد")

        try:
            slot_minutes = int(request.POST.get("slot_minutes", 45))
        except (ValueError, TypeError):
            slot_minutes = 45

        try:
            buffer_minutes = int(request.POST.get("buffer_minutes", 0))
        except (ValueError, TypeError):
            buffer_minutes = 0

        try:
            max_daily = int(request.POST.get("max_daily_sessions", 8))
        except (ValueError, TypeError):
            max_daily = 8

        slot_minutes = max(5, min(240, slot_minutes))
        buffer_minutes = max(0, min(60, buffer_minutes))
        max_daily = max(1, min(30, max_daily))

        ConsultantSlotSettings.objects.update_or_create(
            consultant=consultant,
            defaults={
                "slot_minutes": slot_minutes,
                "buffer_minutes": buffer_minutes,
                "max_daily_sessions": max_daily,
            },
        )

        log_action(
            request, "update_schedule", consultant,
            description=(
                f"ویرایش برنامه هفتگی {consultant.get_full_name()}"
                + (f" — {len(changes_summary)} تغییر" if changes_summary else "")
            ),
        )

        if is_self and is_consultant and changes_summary:
            log_action(
                request, "consultant_schedule_change", consultant,
                description=(
                    f"مشاور {consultant.get_full_name()} برنامه‌اش را تغییر داد — "
                    + "، ".join(changes_summary[:5])
                    + (" ..." if len(changes_summary) > 5 else "")
                ),
            )
            _notify_schedule_change(
                request,
                "الگوی هفتگی بروزرسانی شد",
                detail=f"{len(changes_summary)} تغییر",
            )

        messages.success(request, "برنامهٔ هفتگی با موفقیت ذخیره شد.")
        return redirect("consultant_weekly_schedule", pk=pk)

    # ===== نمایش =====
    weekdays_names = [
        "شنبه", "یک‌شنبه", "دوشنبه",
        "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه",
    ]

    hours_range = list(range(8, 22))

    today = timezone.localdate()
    today_j = jdatetime.date.fromgregorian(date=today)
    today_weekday = today_j.weekday()

    next_dates = {}
    for weekday in range(7):
        days_ahead = (weekday - today_weekday) % 7
        target_date = today + timedelta(days=days_ahead)
        j_date = jdatetime.date.fromgregorian(date=target_date)
        next_dates[weekday] = {
            "gregorian": target_date,
            "jalali": j_date,
            "jalali_str": j_date.strftime("%Y/%m/%d"),
            "is_today": days_ahead == 0,
        }

    days_data = []
    for weekday in range(7):
        schedule = ConsultantWeeklySchedule.objects.filter(
            consultant=consultant,
            weekday=weekday,
        ).first()

        active_hours = []
        if schedule and schedule.is_active:
            try:
                start_h = schedule.start_time.hour
                end_h = schedule.end_time.hour
                if schedule.end_time.minute > 0:
                    end_h += 1

                blocked_set = set(schedule.blocked_hours or [])

                for h in hours_range:
                    if start_h <= h < end_h:
                        is_blocked = h in blocked_set
                        active_hours.append({
                            "hour": h,
                            "state": "blocked" if is_blocked else "active",
                            "clickable": True,
                        })
                    else:
                        active_hours.append({
                            "hour": h,
                            "state": "disabled",
                            "clickable": False,
                        })
            except Exception:
                active_hours = [{"hour": h, "state": "disabled", "clickable": False} for h in hours_range]
        else:
            active_hours = [{"hour": h, "state": "disabled", "clickable": False} for h in hours_range]

        days_data.append({
            "weekday": weekday,
            "name": weekdays_names[weekday],
            "next_date": next_dates[weekday],
            "is_active": schedule.is_active if schedule else False,
            "start": schedule.start_time.strftime("%H:%M") if schedule and schedule.start_time else "08:00",
            "end": schedule.end_time.strftime("%H:%M") if schedule and schedule.end_time else "14:00",
            "blocked_hours": schedule.blocked_hours if schedule else [],
            "hours": active_hours,
        })

    slot_settings, _ = ConsultantSlotSettings.objects.get_or_create(
        consultant=consultant,
        defaults={
            "slot_minutes": 45,
            "buffer_minutes": 0,
            "max_daily_sessions": 8,
        },
    )

    return render(request, "accounts/consultant_weekly_schedule.html", {
        "consultant": consultant,
        "days_data": days_data,
        "slot_settings": slot_settings,
        "hours_range": hours_range,
        "is_self": is_self,
    })


def consultant_month_schedule(request, pk):
    """نمایش تقویم ماهانه مشاور."""
    if not request.user.is_authenticated:
        return redirect("login")

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    is_manager = role == "manager"
    is_secretary = role == "secretary"
    is_consultant = role == "consultant"

    can_edit = is_manager or is_secretary or (is_self and is_consultant)

    if not can_edit:
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ...services import get_month_schedule, get_prev_next_month

    today_j = jdatetime.date.fromgregorian(date=timezone.localdate())

    try:
        year = int(request.GET.get("y", today_j.year))
        month = int(request.GET.get("m", today_j.month))
    except (ValueError, TypeError):
        year, month = today_j.year, today_j.month

    if not (1 <= month <= 12):
        month = today_j.month
    if not (1300 <= year <= 1500):
        year = today_j.year

    month_data = get_month_schedule(consultant, year, month)
    prev_m, next_m = get_prev_next_month(year, month)

    return render(request, "accounts/consultant_month_schedule.html", {
        "consultant": consultant,
        "month_data": month_data,
        "prev_month": prev_m,
        "next_month": next_m,
        "current_year": year,
        "current_month": month,
        "is_self": is_self,
    })