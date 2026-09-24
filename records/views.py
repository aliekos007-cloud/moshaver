from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import medical_view_required, medical_edit_required
from audit.models import log_action
from patients.models import Patient
from clinic.models import ClinicSettings
from .models import Visit
from .forms import VisitForm


@medical_edit_required
def visit_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == "POST":
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.physician = request.user
            visit.save()
            log_action(request, "create", visit, description=f"ثبت مراجعه برای {patient.full_name}")
            return redirect("visit_detail", pk=visit.pk)
    else:
        form = VisitForm()
    return render(request, "records/visit_form.html", {"form": form, "patient": patient})


@medical_view_required
def visit_detail(request, pk):
    visit = get_object_or_404(
        Visit.objects.select_related("patient", "physician"), pk=pk,
    )
    return render(request, "records/visit_detail.html", {"visit": visit})


@medical_view_required
def visit_print(request, pk):
    visit = get_object_or_404(
        Visit.objects.select_related("patient", "physician"), pk=pk,
    )
    clinic = ClinicSettings.get()
    log_action(request, "print", visit, description="چاپ نسخه")
    return render(request, "records/visit_print.html", {
        "visit": visit,
        "clinic": clinic,
    })