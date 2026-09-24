from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import medical_view_required, medical_edit_required
from audit.models import log_action
from .models import Patient
from .forms import PatientForm


@login_required
def patient_list(request):
    q = request.GET.get("q", "").strip()
    qs = Patient.objects.all()
    if q:
        qs = qs.filter(
            Q(file_number__icontains=q)
            | Q(national_code__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(mobile__icontains=q)
        )
    return render(request, "patients/list.html", {"patients": qs, "q": q})


@medical_edit_required
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            p = form.save()
            log_action(request, "create", p, description="ثبت بیمار جدید")
            return redirect("patient_detail", pk=p.pk)
    else:
        form = PatientForm()
    return render(request, "patients/form.html", {"form": form, "title": "ثبت بیمار جدید"})


@medical_edit_required
def patient_edit(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            log_action(request, "update", p, description="ویرایش پرونده بیمار")
            return redirect("patient_detail", pk=p.pk)
    else:
        form = PatientForm(instance=p)
    return render(request, "patients/form.html", {"form": form, "title": f"ویرایش {p.full_name}"})


@login_required
def patient_detail(request, pk):
    from accounts import permissions
    p = get_object_or_404(Patient, pk=pk)
    visits = p.visits.select_related("physician").all()
    log_action(request, "view", p, description="مشاهده پرونده بیمار")
    return render(request, "patients/detail.html", {
        "patient": p,
        "visits": visits,
        "can_view_medical": permissions.can_view_medical(request.user),
        "can_edit_medical": permissions.can_edit_medical(request.user),
    })