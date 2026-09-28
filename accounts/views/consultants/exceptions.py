"""مرخصی و استثناهای برنامه مشاور."""
from datetime import datetime, timedelta

import jdatetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from ...models import User
from audit.models import log_action
from ._helpers import _notify_schedule_change


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

    from ...models import ConsultantScheduleOverride

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

    from ...models import ConsultantScheduleOverride

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
        _notify_schedule_change(
            request,
            "مرخصی جدید ثبت شد",
            detail=range_str,
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

    from ...models import ConsultantScheduleOverride

    exc = get_object_or_404(ConsultantScheduleOverride, pk=exc_id, consultant=consultant)

    exc_info = f"{exc.from_date} تا {exc.to_date}"
    exc.delete()

    log_action(
        request, "delete_exception", consultant,
        description=f"حذف استثنا برای {consultant.get_full_name()}: {exc_info}",
    )

    if is_self and role == "consultant":
        _notify_schedule_change(
            request,
            "مرخصی حذف شد",
            detail=exc_info,
        )

    messages.success(request, "استثنا حذف شد.")
    return redirect("consultant_exceptions", pk=pk)