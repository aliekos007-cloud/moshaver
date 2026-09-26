"""مدیریت سطح مشاور و برنامه‌ریزی هفتگی."""
import json
import jdatetime
from datetime import datetime, timedelta

from datetime import timedelta

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse

from ..models import User, ConsultantLevel
from ..forms import ConsultantLevelForm
from audit.models import log_action


# ==================================================
# مدیریت سطوح مشاور
# ==================================================

def _can_manage_levels(user):
    return user.is_authenticated and user.role in ("manager", "secretary")


def consultant_level_list(request):
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    levels = ConsultantLevel.objects.all().order_by("order", "name")

    levels_data = []
    for level in levels:
        consultant_count = User.objects.filter(
            consultant_level=level,
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
    if not _can_manage_levels(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    level = get_object_or_404(ConsultantLevel, pk=pk)

    if request.method == "POST":
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


# ==================================================
# لیست مشاوران با برنامه
# ==================================================

def consultants_schedule_list(request):
    """لیست همهٔ مشاوران با خلاصهٔ برنامه هفتگی."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary"):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ..models import ConsultantWeeklySchedule, ConsultantSlotSettings

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


# ==================================================
# برنامه هفتگی مشاور
# ==================================================

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

    from ..models import ConsultantWeeklySchedule, ConsultantSlotSettings
    from records.models import Session
    import jdatetime

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

        messages.success(request, "برنامهٔ هفتگی با موفقیت ذخیره شد.")
        return redirect("consultant_weekly_schedule", pk=pk)

    # ===== نمایش =====
    weekdays_names = [
        "شنبه", "یک‌شنبه", "دوشنبه",
        "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه",
    ]

    hours_range = list(range(8, 22))

    # ===== محاسبهٔ تاریخ روز بعدی هر روز هفته =====
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


# ==================================================
# مرخصی و استثناها
# ==================================================

def consultant_exceptions(request, pk):
    """لیست و مدیریت استثناهای برنامه مشاور."""
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

    from ..models import ConsultantScheduleOverride

    today = timezone.localdate()

    exceptions = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        to_date__gte=today - timedelta(days=30),
    ).order_by("-from_date")

    exceptions_data = []
    for exc in exceptions:
        days_count = (exc.to_date - exc.from_date).days + 1

        if exc.to_date < today:
            status = "past"
        elif exc.from_date > today:
            status = "future"
        else:
            status = "current"

        exceptions_data.append({
            "exc": exc,
            "days_count": days_count,
            "status": status,
        })

    return render(request, "accounts/consultant_exceptions.html", {
        "consultant": consultant,
        "exceptions_data": exceptions_data,
        "is_self": is_self,
        "today": today,
    })


@require_POST
def consultant_exception_create(request, pk):
    """افزودن استثنای جدید."""
    if not request.user.is_authenticated:
        return redirect("login")

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    can_edit = role in ("manager", "secretary") or (is_self and role == "consultant")

    if not can_edit:
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    from ..models import ConsultantScheduleOverride

    from_date_str = request.POST.get("from_date", "").strip()
    to_date_str = request.POST.get("to_date", "").strip()
    exception_type = request.POST.get("exception_type", "off")
    custom_start = request.POST.get("custom_start", "").strip()
    custom_end = request.POST.get("custom_end", "").strip()
    reason = request.POST.get("reason", "").strip()[:200]

    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        messages.error(request, "تاریخ نامعتبر است.")
        return redirect("consultant_exceptions", pk=pk)

    if to_date < from_date:
        messages.error(request, "تاریخ پایان نمی‌تواند قبل از شروع باشد.")
        return redirect("consultant_exceptions", pk=pk)

    is_off = exception_type == "off"

    if not is_off:
        if not custom_start or not custom_end:
            messages.error(request, "برای ساعت ویژه، وارد کردن ساعت شروع و پایان الزامی است.")
            return redirect("consultant_exceptions", pk=pk)

    conflicts = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=to_date,
        to_date__gte=from_date,
    )

    if conflicts.exists():
        messages.warning(
            request,
            "⚠️ این بازه با استثنای قبلی تداخل دارد. لطفاً ابتدا استثنای قبلی را حذف کنید."
        )
        return redirect("consultant_exceptions", pk=pk)

    from records.models import Session

    conflicting_sessions = Session.objects.filter(
        consultant=consultant,
        status__in=["scheduled", "in_progress", "paused"],
        scheduled_start__date__gte=from_date,
        scheduled_start__date__lte=to_date,
    ).count()

    if conflicting_sessions > 0 and is_off:
        messages.warning(
            request,
            f"⚠️ توجه: {conflicting_sessions} نوبت رزرو‌شده در این بازه وجود دارد. "
            "استثنا ثبت شد ولی نوبت‌ها را بررسی کنید."
        )

    exc = ConsultantScheduleOverride.objects.create(
        consultant=consultant,
        from_date=from_date,
        to_date=to_date,
        is_off=is_off,
        custom_start=custom_start if custom_start else None,
        custom_end=custom_end if custom_end else None,
        reason=reason,
        created_by=request.user,
    )

    # ===== تبدیل به تاریخ شمسی =====
    import jdatetime
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]

    j_from = jdatetime.date.fromgregorian(date=from_date)
    j_to = jdatetime.date.fromgregorian(date=to_date)

    from_str = f"{j_from.day} {months[j_from.month - 1]}"
    to_str = f"{j_to.day} {months[j_to.month - 1]} {j_to.year}"

    if from_date == to_date:
        range_str = f"{from_str} {j_from.year}"
    else:
        range_str = f"{from_str} تا {to_str}"

    log_action(
        request, "create_exception", consultant,
        description=f"ثبت استثنا برای {consultant.get_full_name()}: "
                    f"{range_str} — "
                    f"{'تعطیل' if is_off else f'ساعت ویژه {custom_start}-{custom_end}'}",
    )

    if is_self and role == "consultant":
        log_action(
            request, "consultant_schedule_change", consultant,
            description=(
                f"مشاور {consultant.get_full_name()} استثنا ثبت کرد: "
                f"{range_str} — "
                f"{'تعطیل' if is_off else 'ساعت ویژه'}"
            ),
        )

    messages.success(request, "استثنا با موفقیت ثبت شد.")
    return redirect("consultant_exceptions", pk=pk)


@require_POST
def consultant_exception_delete(request, pk, exc_id):
    """حذف استثنا."""
    if not request.user.is_authenticated:
        return redirect("login")

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    can_edit = role in ("manager", "secretary") or (is_self and role == "consultant")

    if not can_edit:
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    from ..models import ConsultantScheduleOverride

    exc = get_object_or_404(ConsultantScheduleOverride, pk=exc_id, consultant=consultant)

    exc_info = f"{exc.from_date} تا {exc.to_date}"
    exc.delete()

    log_action(
        request, "delete_exception", consultant,
        description=f"حذف استثنا برای {consultant.get_full_name()}: {exc_info}",
    )

    messages.success(request, "استثنا حذف شد.")
    return redirect("consultant_exceptions", pk=pk)

# ==================================================
# تقویم ماهانه مشاور
# ==================================================

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

    from ..services import get_month_schedule, get_prev_next_month
    import jdatetime

    # ===== تعیین ماه =====
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

    # ===== داده‌های ماه =====
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


@require_POST
def api_save_day_schedule(request, pk):
    """API: ذخیرهٔ برنامهٔ یک روز."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    can_edit = role in ("manager", "secretary") or (is_self and role == "consultant")

    if not can_edit:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from ..models import ConsultantScheduleOverride
    import json as json_lib

    # ===== پارس ورودی =====
    try:
        data = json_lib.loads(request.body)
    except (json_lib.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "error": "داده نامعتبر."}, status=400)

    date_str = data.get("date", "").strip()
    is_active = data.get("is_active", True)
    start_str = (data.get("start") or "").strip()
    end_str = (data.get("end") or "").strip()
    blocked_hours = data.get("blocked_hours", [])
    note = (data.get("note") or "").strip()[:200]

    if not date_str:
        return JsonResponse({"ok": False, "error": "تاریخ ارسال نشده."}, status=400)

    # ===== پارس تاریخ =====
    from datetime import datetime as dt
    try:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "تاریخ نامعتبر."}, status=400)

    # ===== قفل گذشته =====
    today = timezone.localdate()
    if target_date < today:
        return JsonResponse({
            "ok": False,
            "error": "نمی‌توانید روزهای گذشته را تغییر دهید."
        }, status=400)

    # ===== اعتبارسنجی ساعت‌ها =====
    if is_active:
        if not start_str or not end_str:
            return JsonResponse({
                "ok": False,
                "error": "ساعت شروع و پایان الزامی است."
            }, status=400)

        try:
            s_h, s_m = map(int, start_str.split(":"))
            e_h, e_m = map(int, end_str.split(":"))
            if not (0 <= s_h <= 23 and 0 <= s_m <= 59 and 0 <= e_h <= 23 and 0 <= e_m <= 59):
                raise ValueError
            if (s_h, s_m) >= (e_h, e_m):
                return JsonResponse({
                    "ok": False,
                    "error": "ساعت شروع باید قبل از پایان باشد."
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "ساعت نامعتبر."}, status=400)

    # ===== پارس blocked_hours =====
    try:
        blocked_hours = sorted(set(
            int(h) for h in blocked_hours if 0 <= int(h) <= 23
        ))
    except (ValueError, TypeError):
        blocked_hours = []

    # ===== حذف Overrideهای قبلی در این بازه =====
    ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=target_date,
        to_date__gte=target_date,
    ).delete()

    # ===== ساخت Override جدید =====
    override = ConsultantScheduleOverride.objects.create(
        consultant=consultant,
        from_date=target_date,
        to_date=target_date,
        is_off=not is_active,
        custom_start=start_str if is_active else None,
        custom_end=end_str if is_active else None,
        blocked_hours=blocked_hours,
        reason=note,
        created_by=request.user,
    )

    # ===== تبدیل به تاریخ شمسی =====
    import jdatetime
    j_date = jdatetime.date.fromgregorian(date=target_date)
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    jalali_date_str = f"{j_date.day} {months[j_date.month - 1]} {j_date.year}"

    log_action(
        request, "update_day_schedule", consultant,
        description=f"ویرایش برنامهٔ روز {jalali_date_str} — {consultant.get_full_name()}",
    )

    # ===== اعلان به منشی =====
    if is_self and role == "consultant":
        log_action(
            request, "consultant_schedule_change", consultant,
            description=(
                f"مشاور {consultant.get_full_name()} برنامهٔ روز {jalali_date_str} را تغییر داد"
            ),
        )

    return JsonResponse({
        "ok": True,
        "override_id": override.pk,
        "message": "برنامهٔ روز با موفقیت ذخیره شد.",
    })


@require_POST
def api_reset_day_schedule(request, pk):
    """API: بازگشت یک روز به الگوی هفتگی."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    consultant = get_object_or_404(User, pk=pk)

    role = getattr(request.user, "role", None)
    is_self = request.user.pk == consultant.pk
    can_edit = role in ("manager", "secretary") or (is_self and role == "consultant")

    if not can_edit:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from ..models import ConsultantScheduleOverride
    import json as json_lib

    try:
        data = json_lib.loads(request.body)
    except (json_lib.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "error": "داده نامعتبر."}, status=400)

    date_str = data.get("date", "").strip()

    from datetime import datetime as dt
    try:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "تاریخ نامعتبر."}, status=400)

    today = timezone.localdate()
    if target_date < today:
        return JsonResponse({
            "ok": False,
            "error": "نمی‌توانید روزهای گذشته را تغییر دهید."
        }, status=400)

    deleted_count = ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date=target_date,
        to_date=target_date,
    ).delete()[0]

    if deleted_count:
        # ===== تبدیل به تاریخ شمسی =====
        import jdatetime
        j_date = jdatetime.date.fromgregorian(date=target_date)
        months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
        ]
        jalali_date_str = f"{j_date.day} {months[j_date.month - 1]} {j_date.year}"

        log_action(
            request, "reset_day_schedule", consultant,
            description=f"بازگشت برنامهٔ روز {jalali_date_str} به الگو — {consultant.get_full_name()}",
        )
        if is_self and role == "consultant":
            log_action(
                request, "consultant_schedule_change", consultant,
                description=(
                    f"مشاور {consultant.get_full_name()} برنامهٔ روز {jalali_date_str} را به الگو بازگرداند"
                ),
            )

    return JsonResponse({
        "ok": True,
        "message": "برنامهٔ روز به الگوی هفتگی بازگشت.",
    })

# ==================================================
# جست‌وجوی نوبت
# ==================================================

def slot_search(request):
    """جست‌وجوی نوبت خالی برای مشاور."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary"):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ..services import find_nearest_slot, get_days_summary
    import jdatetime

    # ===== لیست مشاوران =====
    consultants = User.objects.filter(
        is_active=True,
        consultant_level__isnull=False,
    ).order_by("last_name", "first_name")

    # ===== مشاور انتخاب‌شده =====
    consultant_id = request.GET.get("consultant")
    selected_consultant = None
    nearest_slot = None
    days_summary = None
    summary_stats = {"total_free": 0, "total_booked": 0}

    if consultant_id:
        try:
            selected_consultant = User.objects.get(pk=consultant_id)
        except (User.DoesNotExist, ValueError):
            pass

    if selected_consultant:
        # نزدیک‌ترین نوبت (تا ۹۰ روز)
        nearest = find_nearest_slot(selected_consultant, max_days=90)

        if nearest["found"]:
            nearest_j = jdatetime.date.fromgregorian(date=nearest["date"])
            nearest_slot = {
                "found": True,
                "date": nearest["date"],
                "date_iso": nearest["date"].isoformat(),
                "date_jalali": nearest_j.strftime("%Y/%m/%d"),
                "date_jalali_full": _jalali_full(nearest["date"]),
                "weekday": _jalali_weekday(nearest["date"]),
                "start": nearest["start"].strftime("%H:%M"),
                "end": nearest["end"].strftime("%H:%M"),
                "days_ahead": nearest["days_ahead"],
                "is_today": nearest["days_ahead"] == 0,
            }
        else:
            nearest_slot = {"found": False}

        # خلاصهٔ ۳۰ روز
        days_raw = get_days_summary(selected_consultant, days=30)

        days_summary = []
        for target_date, info in days_raw.items():
            j_date = jdatetime.date.fromgregorian(date=target_date)

            days_summary.append({
                "date": target_date,
                "date_iso": target_date.isoformat(),
                "date_jalali": j_date,
                "day": j_date.day,
                "month": j_date.month,
                "weekday": j_date.weekday(),
                "is_today": target_date == timezone.localdate(),
                "total": info["total"],
                "free": info["free"],
                "booked": info["booked"],
                "status": info["status"],
            })

            summary_stats["total_free"] += info["free"]
            summary_stats["total_booked"] += info["booked"]

    return render(request, "accounts/slot_search.html", {
        "consultants": consultants,
        "selected_consultant": selected_consultant,
        "nearest_slot": nearest_slot,
        "days_summary": days_summary,
        "summary_stats": summary_stats,
    })


@require_GET
def api_day_slots(request, pk):
    """API: اسلات‌های یه روز برای مودال."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    consultant = get_object_or_404(User, pk=pk)

    date_str = request.GET.get("date", "").strip()
    if not date_str:
        return JsonResponse({"ok": False, "error": "تاریخ ارسال نشده."}, status=400)

    from datetime import datetime as dt
    try:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "تاریخ نامعتبر."}, status=400)

    from ..services import generate_slots
    from iranholidays import off_occasion_solar
    import jdatetime

    slots = generate_slots(consultant, target_date)

    # تعطیلات رسمی
    holiday_name = None
    try:
        j_date = jdatetime.date.fromgregorian(date=target_date)
        holiday = off_occasion_solar(j_date)
        if holiday:
            from ..services import _translate_holiday
            holiday_name = _translate_holiday(holiday)
    except Exception:
        pass

    slots_data = []
    for s in slots:
        slots_data.append({
            "start": s["start"].strftime("%H:%M"),
            "end": s["end"].strftime("%H:%M"),
            "is_free": s["is_free"],
            "status": s["status"],
            "session_id": s["session_id"],
            "client_name": s["client_name"],
        })

    return JsonResponse({
        "ok": True,
        "date_iso": target_date.isoformat(),
        "date_jalali": _jalali_full(target_date),
        "weekday": _jalali_weekday(target_date),
        "is_holiday": holiday_name is not None,
        "holiday_name": holiday_name,
        "slots": slots_data,
        "free_count": len([s for s in slots if s["is_free"]]),
    })


# ==================================================
# ابزارهای کمکی
# ==================================================

def _jalali_full(g_date):
    """مثلاً: ۴ مهر ۱۴۰۵"""
    import jdatetime
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.day} {months[j.month - 1]} {j.year}"


def _jalali_weekday(g_date):
    import jdatetime
    weekdays = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    j = jdatetime.date.fromgregorian(date=g_date)
    return weekdays[j.weekday()]