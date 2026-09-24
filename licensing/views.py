from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.decorators import manager_required
from audit.models import log_action
from .models import License
from .forms import LicenseForm, ActivateLicenseForm


@manager_required
def license_dashboard(request):
    """صفحه اصلی لایسنس — نمایش وضعیت."""
    current = License.get_current()
    history = License.objects.all()[:20]
    return render(request, "licensing/dashboard.html", {
        "license": current,
        "history": history,
    })


@manager_required
def license_create(request):
    if request.method == "POST":
        form = LicenseForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = "active"
            obj.is_active = True
            obj.activated_at = timezone.now()
            if not obj.valid_from:
                from datetime import date
                obj.valid_from = date.today()
            obj.save()
            log_action(request, "create", obj, description=f"صدور لایسنس جدید: {obj.license_key}")
            messages.success(request, f"لایسنس «{obj.license_key}» صادر شد.")
            return redirect("license_dashboard")
    else:
        form = LicenseForm()
    return render(request, "licensing/form.html", {"form": form, "title": "صدور لایسنس جدید"})


@manager_required
def license_edit(request, pk):
    obj = get_object_or_404(License, pk=pk)
    if request.method == "POST":
        form = LicenseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            log_action(request, "update", obj, description=f"ویرایش لایسنس: {obj.license_key}")
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("license_dashboard")
    else:
        form = LicenseForm(instance=obj)
    return render(request, "licensing/form.html", {
        "form": form, "title": f"ویرایش لایسنس {obj.license_key}", "license": obj,
    })


@manager_required
def license_activate(request, pk):
    """فعال‌سازی مجدد."""
    obj = get_object_or_404(License, pk=pk)
    if request.method == "POST":
        duration = int(request.POST.get("duration", 365))
        obj.activate(days=duration)
        log_action(request, "update", obj, description=f"فعال‌سازی لایسنس: {obj.license_key} برای {duration} روز")
        messages.success(request, f"لایسنس برای {duration} روز فعال شد.")
    return redirect("license_dashboard")


@manager_required
def license_deactivate(request, pk):
    obj = get_object_or_404(License, pk=pk)
    if request.method == "POST":
        obj.deactivate()
        log_action(request, "update", obj, description=f"غیرفعال‌سازی لایسنس: {obj.license_key}")
        messages.warning(request, "لایسنس غیرفعال شد.")
    return redirect("license_dashboard")


@manager_required
def license_delete(request, pk):
    obj = get_object_or_404(License, pk=pk)
    if request.method == "POST":
        key = obj.license_key
        obj.delete()
        log_action(request, "delete", description=f"حذف لایسنس: {key}")
        messages.success(request, "لایسنس حذف شد.")
    return redirect("license_dashboard")


@manager_required
def license_enter_key(request):
    """صفحه‌ی وارد کردن کلید لایسنس (فعال‌سازی نصب جدید)."""
    if request.method == "POST":
        form = ActivateLicenseForm(request.POST)
        if form.is_valid():
            key = form.cleaned_data["license_key"]
            try:
                obj = License.objects.get(license_key=key)
                if obj.is_active:
                    messages.info(request, f"این لایسنس قبلاً فعال است. اعتبار: {obj.valid_until}")
                else:
                    obj.activate(days=365)
                    log_action(request, "update", obj, description=f"فعال‌سازی با کلید: {key}")
                    messages.success(request, f"لایسنس «{key}» با موفقیت فعال شد.")
                return redirect("license_dashboard")
            except License.DoesNotExist:
                messages.error(request, "کلید لایسنس معتبر نیست یا در این نصب وجود ندارد.")
    else:
        form = ActivateLicenseForm()
    return render(request, "licensing/enter_key.html", {"form": form})


@manager_required
def trial_status(request):
    """صفحه‌ی وضعیت trial."""
    from .services import get_trial_info, get_install_state
    trial = get_trial_info()
    state = get_install_state()
    return render(request, "licensing/trial_status.html", {
        "trial": trial,
        "state": state,
    })