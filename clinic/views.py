import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.decorators import medical_edit_required
from audit.models import log_action
from .models import ClinicSettings, Room
from .forms import ClinicSettingsForm, RoomForm


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
    """لیست اتاق‌ها به‌صورت گرید."""
    if not _can_manage_rooms(request.user):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    rooms = Room.objects.all().order_by("order", "id")

    # آماده‌سازی اطلاعات هر اتاق
    rooms_data = []
    for room in rooms:
        # جلسهٔ فعال فعلی این اتاق (اگر Session داریم)
        current_session = None
        try:
            from records.models import Session
            current_session = Session.objects.filter(
                room=room,
                status__in=["in_progress", "paused"],
            ).select_related("consultant", "client").first()
        except Exception:
            pass

        rooms_data.append({
            "room": room,
            "current_session": current_session,
            "is_occupied": current_session is not None,
        })

    return render(request, "clinic/room_list.html", {
        "rooms_data": rooms_data,
        "total": len(rooms_data),
    })


def room_create(request):
    """ساخت اتاق جدید."""
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
    """ویرایش اتاق."""
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
    """فعال/غیرفعال کردن اتاق."""
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
    """حذف اتاق."""
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
    """ذخیرهٔ ترتیب جدید اتاق‌ها (AJAX)."""
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

    log_action(
        request, "update", None,
        description=f"تنظیم ترتیب {updated} اتاق",
    )
    return JsonResponse({"ok": True, "updated": updated})