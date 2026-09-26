import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from accounts.decorators import medical_edit_required
from audit.models import log_action
from .models import (
    ClinicSettings, Room,
    ConsultantDailyPresence, ConsultantRoomChange,
)
from .forms import (
    ClinicSettingsForm, RoomForm,
    PresenceRegisterForm, ChangeRoomForm,
)


# ==================================================
# تنظیمات مرکز
# ==================================================

@medical_edit_required
def clinic_settings(request):
    instance = ClinicSettings.get()
    if request.method == "POST":
        form = ClinicSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            log_action(request, "update", instance, description="ویرایش تنظیمات مرکز")
            messages.success(request, "تنظیمات مرکز با موفقیت ذخیره شد.")
            return redirect("clinic_settings")
    else:
        form = ClinicSettingsForm(instance=instance)
    return render(request, "clinic/settings.html", {"form": form})


# ==================================================
# مدیریت اتاق‌ها
# ==================================================

def _can_manage_rooms(user):
    return user.is_authenticated and user.role in ("manager", "secretary")


def room_list(request):
    """لیست اتاق‌ها به‌صورت گرید — با نمایش وضعیت زنده."""
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    from records.models import Session as TherapySession

    today = timezone.localdate()
    rooms = Room.objects.all().order_by("order", "id")

    rooms_data = []
    for room in rooms:
        # ===== چک جلسهٔ فعال در این اتاق =====
        current_session = TherapySession.objects.filter(
            room=room,
            status__in=["in_progress", "paused"],
        ).select_related("consultant", "client").first()

        # ===== چک جلسهٔ بعدی امروز (در انتظار) =====
        next_session = None
        if not current_session:
            next_session = TherapySession.objects.filter(
                room=room,
                scheduled_start__date=today,
                status="scheduled",
            ).select_related("consultant", "client").order_by("scheduled_start").first()

        # ===== تعیین وضعیت =====
        if current_session:
            status = "in_session"
        elif next_session:
            status = "scheduled"
        else:
            status = "free"

        rooms_data.append({
            "room": room,
            "current_session": current_session,
            "next_session": next_session,
            "status": status,
            "is_occupied": current_session is not None,
        })

    return render(request, "clinic/room_list.html", {
        "rooms_data": rooms_data,
        "total": len(rooms_data),
        "today": today,
    })


def room_create(request):
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            log_action(request, "create", room, description=f"ساخت اتاق جدید: {room.name}")
            messages.success(request, f"اتاق «{room.name}» با موفقیت ساخته شد.")
            return redirect("room_list")
    else:
        form = RoomForm()

    return render(request, "clinic/room_form.html", {
        "form": form,
        "title": "اتاق جدید",
        "is_edit": False,
    })


def room_edit(request, pk):
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            log_action(request, "update", room, description=f"ویرایش اتاق: {room.name}")
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("room_list")
    else:
        form = RoomForm(instance=room)

    return render(request, "clinic/room_form.html", {
        "form": form,
        "title": f"ویرایش {room.name}",
        "room": room,
        "is_edit": True,
    })


def room_toggle(request, pk):
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        room.is_active = not room.is_active
        room.save()
        status = "فعال" if room.is_active else "غیرفعال"
        log_action(request, "update", room, description=f"{status} کردن اتاق: {room.name}")
        messages.success(request, f"اتاق «{room.name}» {status} شد.")
    return redirect("room_list")


def room_delete(request, pk):
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        if room.sessions.exists() or room.presences.exists():
            messages.error(
                request,
                f"اتاق «{room.name}» قابل حذف نیست چون در جلسات یا حضورها استفاده شده. "
                "می‌توانید آن را غیرفعال کنید."
            )
            return redirect("room_list")

        name = room.name
        room.delete()
        log_action(request, "delete", None, description=f"حذف اتاق: {name}")
        messages.success(request, f"اتاق «{name}» حذف شد.")
        return redirect("room_list")

    return render(request, "clinic/room_confirm_delete.html", {"room": room})


@require_POST
def room_reorder(request):
    if not _can_manage_rooms(request.user):
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    try:
        data = json.loads(request.body)
        order_ids = data.get("order", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "داده نامعتبر."}, status=400)

    updated = 0
    for idx, room_id in enumerate(order_ids, start=1):
        count = Room.objects.filter(pk=room_id).update(order=idx)
        updated += count

    log_action(request, "update", None, description=f"تنظیم ترتیب {updated} اتاق")
    return JsonResponse({"ok": True, "updated": updated})


# ==================================================
# مدیریت حضور مشاور
# ==================================================

def _can_manage_presence(user):
    return user.is_authenticated and user.role in ("manager", "secretary")


def presence_list(request):
    """لیست حضور امروز."""
    if not _can_manage_presence(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    today = timezone.localdate()

    presences = ConsultantDailyPresence.objects.filter(
        date=today,
    ).select_related("consultant", "room").order_by("arrived_at")

    # مشاوران بدون حضور
    from accounts.models import User, Role
    present_ids = presences.values_list("consultant_id", flat=True)
    absent_consultants = User.objects.filter(
        role=Role.CONSULTANT,
        is_active=True,
    ).exclude(id__in=present_ids).order_by("last_name", "first_name")

    # آمار
    total_consultants = User.objects.filter(role=Role.CONSULTANT, is_active=True).count()
    present_count = presences.count()

    return render(request, "clinic/presence_list.html", {
        "today": today,
        "presences": presences,
        "absent_consultants": absent_consultants,
        "total_consultants": total_consultants,
        "present_count": present_count,
    })


def presence_register(request):
    """ثبت حضور مشاور جدید."""
    if not _can_manage_presence(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    if request.method == "POST":
        form = PresenceRegisterForm(request.POST)
        if form.is_valid():
            consultant = form.cleaned_data["consultant"]
            room = form.cleaned_data.get("room")
            note = form.cleaned_data.get("note", "")

            presence = ConsultantDailyPresence.objects.create(
                consultant=consultant,
                date=timezone.localdate(),
                room=room,
                arrived_at=timezone.now(),
                status="present",
                note=note,
            )

            log_action(
                request, "create", presence,
                description=f"ثبت حضور: {consultant.get_full_name()} — اتاق {room.name if room else 'بدون اتاق'}",
            )

            messages.success(
                request,
                f"حضور «{consultant.get_full_name()}» با موفقیت ثبت شد."
            )
            return redirect("presence_list")
    else:
        form = PresenceRegisterForm()

    return render(request, "clinic/presence_register.html", {"form": form})


def presence_change_room(request, pk):
    """تغییر اتاق مشاور."""
    if not _can_manage_presence(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    presence = get_object_or_404(
        ConsultantDailyPresence.objects.select_related("consultant", "room"),
        pk=pk,
    )

    if request.method == "POST":
        form = ChangeRoomForm(request.POST, current_presence=presence)
        if form.is_valid():
            old_room = presence.room
            new_room = form.cleaned_data.get("room")
            note = form.cleaned_data.get("note", "")

            # ثبت تاریخچه
            ConsultantRoomChange.objects.create(
                consultant=presence.consultant,
                date=presence.date,
                from_room=old_room,
                to_room=new_room,
                changed_at=timezone.now(),
                changed_by=request.user,
                note=note,
            )

            presence.room = new_room
            presence.save()

            log_action(
                request, "update", presence,
                description=f"تغییر اتاق {presence.consultant.get_full_name()}: "
                            f"{old_room.name if old_room else '—'} → {new_room.name if new_room else '—'}",
            )

            messages.success(
                request,
                f"اتاق «{presence.consultant.get_full_name()}» به «{new_room.name if new_room else 'بدون اتاق'}» تغییر یافت."
            )
            return redirect("presence_list")
    else:
        form = ChangeRoomForm(current_presence=presence)

    return render(request, "clinic/presence_change_room.html", {
        "form": form,
        "presence": presence,
    })


@require_POST
def presence_checkout(request, pk):
    """ثبت خروج مشاور از مرکز."""
    if not _can_manage_presence(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    presence = get_object_or_404(ConsultantDailyPresence, pk=pk)

    # چک جلسهٔ فعال
    from records.models import Session
    active = Session.objects.filter(
        consultant=presence.consultant,
        status__in=["in_progress", "paused"],
    ).exists()

    if active:
        messages.error(
            request,
            f"«{presence.consultant.get_full_name()}» جلسهٔ فعال دارد. "
            "ابتدا جلسه را ببندید."
        )
        return redirect("presence_list")

    presence.left_at = timezone.now()
    presence.status = "left"
    presence.save()

    log_action(
        request, "update", presence,
        description=f"ثبت خروج: {presence.consultant.get_full_name()}",
    )
    messages.success(
        request,
        f"خروج «{presence.consultant.get_full_name()}» ثبت شد."
    )
    return redirect("presence_list")


@require_POST
def presence_toggle_break(request, pk):
    """استراحت / بازگشت از استراحت."""
    if not _can_manage_presence(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    presence = get_object_or_404(ConsultantDailyPresence, pk=pk)

    if presence.status == "on_break":
        presence.status = "present"
        msg = "بازگشت از استراحت"
    elif presence.status in ("present", "in_session"):
        presence.status = "on_break"
        msg = "شروع استراحت"
    else:
        messages.error(request, "وضعیت فعلی قابل تغییر نیست.")
        return redirect("presence_list")

    presence.save()
    log_action(request, "update", presence, description=f"{msg}: {presence.consultant.get_full_name()}")
    messages.success(request, f"{msg} «{presence.consultant.get_full_name()}» ثبت شد.")
    return redirect("presence_list")
# ==================================================
# API — اتاق فعلی مشاور
# ==================================================

@require_GET
def api_consultant_room(request, consultant_id):
    """اتاق فعلی مشاور رو برمی‌گرداند (بر اساس حضور امروز)."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from accounts.models import User
    from .models import ConsultantDailyPresence

    try:
        consultant = User.objects.get(pk=consultant_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "مشاور یافت نشد."}, status=404)

    today = timezone.localdate()

    presence = ConsultantDailyPresence.objects.filter(
        consultant=consultant,
        date=today,
        status__in=["present", "in_session", "on_break"],
    ).select_related("room").first()

    # ===== چک: مشاور در جلسهٔ فعال است؟ =====
    from records.models import Session as TherapySession

    active_session = TherapySession.objects.filter(
        consultant=consultant,
        status__in=["in_progress", "paused"],
    ).select_related("client").first()

    is_busy = active_session is not None

    if not presence:
        return JsonResponse({
            "ok": True,
            "present": False,
            "is_busy": is_busy,
            "busy_with": active_session.client.full_name if active_session else None,
            "message": f"{consultant.get_full_name()} امروز حضور خود را ثبت نکرده است.",
        })

    if not presence.room:
        return JsonResponse({
            "ok": True,
            "present": True,
            "has_room": False,
            "is_busy": is_busy,
            "busy_with": active_session.client.full_name if active_session else None,
            "message": f"{consultant.get_full_name()} حاضر است ولی اتاق ندارد.",
        })

    return JsonResponse({
        "ok": True,
        "present": True,
        "has_room": True,
        "is_busy": is_busy,
        "busy_with": active_session.client.full_name if active_session else None,
        "room_id": presence.room.id,
        "room_name": presence.room.name,
        "status": presence.get_status_display(),
    })
# ==================================================
# API — اسلات‌های آزاد مشاور
# ==================================================

@require_GET
def api_consultant_slots(request, consultant_id):
    """
    اسلات‌های آزاد مشاور در یک تاریخ.
    Query params:
      - date: تاریخ میلادی (YYYY-MM-DD) یا جلالی (1405-07-03)
    """
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from accounts.models import User
    from accounts.services import generate_slots

    try:
        consultant = User.objects.get(pk=consultant_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "مشاور یافت نشد."}, status=404)

    # ===== پارس تاریخ =====
    date_str = request.GET.get("date", "").strip()
    if not date_str:
        return JsonResponse({"ok": False, "error": "تاریخ ارسال نشده."}, status=400)

    target_date = _parse_date(date_str)
    if not target_date:
        return JsonResponse({"ok": False, "error": "تاریخ نامعتبر."}, status=400)

    # ===== تولید اسلات‌ها =====
    slots = generate_slots(consultant, target_date)

    # ===== تبدیل به JSON =====
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

    free_count = len([s for s in slots if s["is_free"]])

    return JsonResponse({
        "ok": True,
        "date": target_date.isoformat(),
        "total": len(slots),
        "free_count": free_count,
        "slots": slots_data,
    })


# ==================================================
# API — نزدیک‌ترین نوبت خالی
# ==================================================

@require_GET
def api_nearest_slot(request, consultant_id):
    """نزدیک‌ترین نوبت خالی مشاور."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from accounts.models import User
    from accounts.services import find_nearest_slot

    try:
        consultant = User.objects.get(pk=consultant_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "مشاور یافت نشد."}, status=404)

    result = find_nearest_slot(consultant, max_days=90)

    if not result["found"]:
        return JsonResponse({
            "ok": True,
            "found": False,
            "message": "در ۹۰ روز آینده نوبت خالی وجود ندارد.",
        })

    # فرمت تاریخ برای نمایش
    import jdatetime
    j_date = jdatetime.date.fromgregorian(date=result["date"])

    return JsonResponse({
        "ok": True,
        "found": True,
        "date": result["date"].isoformat(),
        "date_jalali": j_date.strftime("%Y/%m/%d"),
        "start": result["start"].strftime("%H:%M"),
        "end": result["end"].strftime("%H:%M"),
        "days_ahead": result["days_ahead"],
    })


# ==================================================
# API — خلاصهٔ روزها
# ==================================================

@require_GET
def api_days_summary(request, consultant_id):
    """
    خلاصهٔ وضعیت روزها.
    Query params:
      - days: تعداد روز (پیش‌فرض ۳۰)
    """
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "دسترسی مجاز نیست."}, status=403)

    from accounts.models import User
    from accounts.services import get_days_summary

    try:
        consultant = User.objects.get(pk=consultant_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "مشاور یافت نشد."}, status=404)

    try:
        days = int(request.GET.get("days", 30))
    except (ValueError, TypeError):
        days = 30
    days = max(1, min(365, days))

    summary = get_days_summary(consultant, days=days)

    # تبدیل به JSON
    import jdatetime
    days_data = []
    total_free = 0
    total_booked = 0

    for target_date, info in summary.items():
        j_date = jdatetime.date.fromgregorian(date=target_date)

        days_data.append({
            "date": target_date.isoformat(),
            "date_jalali": j_date.strftime("%Y/%m/%d"),
            "day": j_date.day,
            "month": j_date.month,
            "year": j_date.year,
            "weekday": j_date.weekday(),  # 0=شنبه
            "total": info["total"],
            "free": info["free"],
            "booked": info["booked"],
            "status": info["status"],
        })

        total_free += info["free"]
        total_booked += info["booked"]

    return JsonResponse({
        "ok": True,
        "days": days_data,
        "total_free": total_free,
        "total_booked": total_booked,
    })


# ==================================================
# ابزار کمکی
# ==================================================

def _parse_date(date_str):
    """پارس تاریخ میلادی یا جلالی."""
    from datetime import datetime as dt

    # حالت ۱: میلادی YYYY-MM-DD
    try:
        return dt.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        pass

    # حالت ۲: جلالی YYYY/MM/DD
    try:
        import jdatetime
        parts = date_str.replace("-", "/").split("/")
        if len(parts) == 3:
            j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            return j_date.togregorian()
    except (ValueError, TypeError):
        pass

    return None