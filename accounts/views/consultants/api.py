"""APIهای ذخیره/ریست برنامه روزانه مشاور."""
import json as json_lib
from datetime import datetime as dt

import jdatetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from ...models import User
from audit.models import log_action
from ._helpers import _notify_schedule_change


def _to_jalali_str(g_date):
    """تبدیل تاریخ میلادی به رشته شمسی مثل: ۴ مهر ۱۴۰۵"""
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.day} {months[j.month - 1]} {j.year}"


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

    from ...models import ConsultantScheduleOverride

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

    try:
        blocked_hours = sorted(set(
            int(h) for h in blocked_hours if 0 <= int(h) <= 23
        ))
    except (ValueError, TypeError):
        blocked_hours = []

    ConsultantScheduleOverride.objects.filter(
        consultant=consultant,
        from_date__lte=target_date,
        to_date__gte=target_date,
    ).delete()

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

    jalali_date_str = _to_jalali_str(target_date)

    log_action(
        request, "update_day_schedule", consultant,
        description=f"ویرایش برنامهٔ روز {jalali_date_str} — {consultant.get_full_name()}",
    )

    if is_self and role == "consultant":
        log_action(
            request, "consultant_schedule_change", consultant,
            description=(
                f"مشاور {consultant.get_full_name()} برنامهٔ روز {jalali_date_str} را تغییر داد"
            ),
        )
        _notify_schedule_change(
            request,
            "برنامه یک روز تغییر کرد",
            detail=jalali_date_str,
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

    from ...models import ConsultantScheduleOverride

    try:
        data = json_lib.loads(request.body)
    except (json_lib.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "error": "داده نامعتبر."}, status=400)

    date_str = data.get("date", "").strip()

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
        jalali_date_str = _to_jalali_str(target_date)

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
            _notify_schedule_change(
                request,
                "برنامه یک روز به پیش‌فرض برگشت",
                detail=jalali_date_str,
            )

    return JsonResponse({
        "ok": True,
        "message": "برنامهٔ روز به الگوی هفتگی بازگشت.",
    })