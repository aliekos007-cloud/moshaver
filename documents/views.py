from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from patients.models import Patient
from .models import PatientDocument
from .forms import PatientDocumentForm


@login_required
def document_upload(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == "POST":
        form = PatientDocumentForm(request.POST, request.FILES, patient=patient)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.patient = patient
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, "مدرک با موفقیت بارگذاری شد.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientDocumentForm(patient=patient)
    return render(request, "documents/upload.html", {"form": form, "patient": patient})


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(PatientDocument, pk=pk)
    patient_pk = doc.patient.pk
    if request.method == "POST":
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "مدرک حذف شد.")
    return redirect("patient_detail", pk=patient_pk)