"""مدیریت سطوح مشاوران."""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ...models import User, ConsultantLevel
from ...forms import ConsultantLevelForm
from audit.models import log_action
from ._helpers import _can_manage_levels


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