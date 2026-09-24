from django.contrib import messages
from django.shortcuts import render, redirect
from accounts.decorators import medical_edit_required
from .models import ClinicSettings
from .forms import ClinicSettingsForm


@medical_edit_required
def clinic_settings(request):
    instance = ClinicSettings.get()
    if request.method == "POST":
        form = ClinicSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات مطب با موفقیت ذخیره شد.")
            return redirect("clinic_settings")
    else:
        form = ClinicSettingsForm(instance=instance)
    return render(request, "clinic/settings.html", {"form": form})