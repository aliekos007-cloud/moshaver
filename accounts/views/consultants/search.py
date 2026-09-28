"""جست‌وجوی نوبت خالی برای مشاور."""
import jdatetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.http import JsonResponse

from ...models import User
from ._helpers import _jalali_full, _jalali_weekday


def slot_search(request):
    """جست‌وجوی نوبت خالی برای مشاور."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary"):
        messages.error(request, "دسترسی به این بخش مجاز نیست.")
        return redirect("dashboard")

    from ...services import find_nearest_slot, get_days_summary

    consultants = User.objects.filter(
        is_active=True,
        consultant_level__isnull=False,
    ).order_by("last_name", "first_name")

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

    from ...services import generate_slots
    import jdatetime

    slots = generate_slots(consultant, target_date)

    holiday_name = None
    try:
        from iranholidays import off_occasion_solar
        j_date = jdatetime.date.fromgregorian(date=target_date)
        holiday = off_occasion_solar(j_date)
        if holiday:
            from ...services import _translate_holiday
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