from datetime import date, timedelta, datetime

import jdatetime
from django.contrib import messages
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from accounts.decorators import appointments_required, medical_edit_required
from audit.models import log_action
from patients.models import Patient
from .models import Appointment, WeeklySchedule, TimeOff
from .forms import AppointmentForm, WeeklyScheduleForm, TimeOffForm
from .services import get_available_slots, get_our_weekday, count_available_slots


@appointments_required
def secretary_dashboard(request):
    today = date.today()
    today_appointments = Appointment.objects.filter(
        date=today,
    ).select_related("patient", "physician").order_by("start_time")

    stats = {
        "total": today_appointments.count(),
        "arrived": today_appointments.filter(status="arrived").count(),
        "waiting": today_appointments.filter(status__in=["scheduled", "confirmed"]).count(),
        "no_show": today_appointments.filter(status="no_show").count(),
        "completed": today_appointments.filter(status="completed").count(),
    }

    our_day = get_our_weekday(today)
    saturday = today - timedelta(days=our_day)
    week_end = saturday + timedelta(days=6)
    week_count = Appointment.objects.filter(
        date__gte=saturday, date__lte=week_end,
        status__in=["scheduled", "confirmed"],
    ).count()

    return render(request, "appointments/secretary_dashboard.html", {
        "today": today,
        "today_appointments": today_appointments,
        "stats": stats,
        "week_count": week_count,
    })


@appointments_required
def appointment_list(request):
    qs = Appointment.objects.select_related("patient", "physician", "created_by")

    status = request.GET.get("status", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    q = request.GET.get("q", "").strip()
    phys_id = request.GET.get("physician", "")

    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if phys_id:
        qs = qs.filter(physician_id=phys_id)
    if q:
        qs = qs.filter(
            models.Q(patient__first_name__icontains=q)
            | models.Q(patient__last_name__icontains=q)
            | models.Q(patient__mobile__icontains=q)
            | models.Q(patient__national_code__icontains=q)
        )

    from accounts.models import User
    physicians = User.objects.filter(role__in=["physician", "manager"])

    return render(request, "appointments/list.html", {
        "appointments": qs[:500],
        "status_filter": status,
        "from_filter": date_from,
        "to_filter": date_to,
        "q": q,
        "physician_filter": phys_id,
        "physicians": physicians,
        "statuses": Appointment.STATUS,
    })


@appointments_required
def appointment_week_view(request):
    ref_date_s = request.GET.get("date", "")
    try:
        ref_date = datetime.strptime(ref_date_s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        ref_date = date.today()

    our_day = get_our_weekday(ref_date)
    saturday = ref_date - timedelta(days=our_day)

    from accounts.models import User
    physicians = User.objects.filter(role__in=["physician", "manager"])
    phys_id = request.GET.get("physician", "")
    physician = physicians.filter(pk=phys_id).first() if phys_id else physicians.first()

    days = []
    for i in range(7):
        d = saturday + timedelta(days=i)
        apts = Appointment.objects.filter(
            date=d,
            status__in=["scheduled", "confirmed", "arrived", "in_progress", "completed"],
        )
        if physician:
            apts = apts.filter(physician=physician)
        apts = apts.select_related("patient", "physician").order_by("start_time")
        days.append({
            "date": d,
            "jdate": jdatetime.date.fromgregorian(date=d),
            "appointments": list(apts),
            "is_today": d == date.today(),
            "available_slots": count_available_slots(physician, d) if physician else 0,
        })

    return render(request, "appointments/week_view.html", {
        "days": days,
        "saturday": saturday,
        "prev_week": saturday - timedelta(days=7),
        "next_week": saturday + timedelta(days=7),
        "physician": physician,
        "physicians": physicians,
        "today": date.today(),
    })


@appointments_required
def appointment_day_view(request):
    date_s = request.GET.get("date", "")
    try:
        target_date = datetime.strptime(date_s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        target_date = date.today()

    from accounts.models import User
    physicians = User.objects.filter(role__in=["physician", "manager"])
    phys_id = request.GET.get("physician", "")
    physician = physicians.filter(pk=phys_id).first() if phys_id else physicians.first()

    slots = get_available_slots(physician, target_date) if physician else []
    jdate = jdatetime.date.fromgregorian(date=target_date)

    return render(request, "appointments/day_view.html", {
        "target_date": target_date,
        "jdate": jdate,
        "slots": slots,
        "physician": physician,
        "physicians": physicians,
        "prev_day": target_date - timedelta(days=1),
        "next_day": target_date + timedelta(days=1),
        "today": date.today(),
    })


@appointments_required
def appointment_create(request, patient_pk=None):
    patient = None
    if patient_pk:
        patient = get_object_or_404(Patient, pk=patient_pk)

    initial = {}
    date_s = request.GET.get("date")
    start_s = request.GET.get("start")
    end_s = request.GET.get("end")
    phys_id = request.GET.get("physician")

    if date_s and start_s and end_s:
        try:
            initial["date"] = datetime.strptime(date_s, "%Y-%m-%d").date()
            initial["start_time"] = datetime.strptime(start_s, "%H:%M").time()
            initial["end_time"] = datetime.strptime(end_s, "%H:%M").time()
        except ValueError:
            pass
    if phys_id:
        initial["physician"] = phys_id

    if request.method == "POST":
        form = AppointmentForm(request.POST, patient=patient)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            if patient:
                obj.patient = patient
            obj.save()
            log_action(request, "create", obj,
                       description=f"ثبت نوبت برای {obj.patient.full_name} در {obj.date} {obj.start_time:%H:%M}")
            messages.success(request, f"نوبت برای {obj.patient.full_name} ثبت شد.")
            return redirect("appointment_detail", pk=obj.pk)
    else:
        form = AppointmentForm(initial=initial, patient=patient)

    return render(request, "appointments/form.html", {
        "form": form, "patient": patient, "title": "نوبت جدید",
    })


@appointments_required
def appointment_detail(request, pk):
    obj = get_object_or_404(
        Appointment.objects.select_related("patient", "physician", "created_by", "visit"), pk=pk,
    )
    return render(request, "appointments/detail.html", {"appointment": obj})


@appointments_required
def appointment_edit(request, pk):
    obj = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            log_action(request, "update", obj, description=f"ویرایش نوبت: {obj.patient.full_name}")
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("appointment_detail", pk=obj.pk)
    else:
        form = AppointmentForm(instance=obj)
    return render(request, "appointments/form.html", {
        "form": form, "patient": obj.patient,
        "title": f"ویرایش نوبت {obj.patient.full_name}", "appointment": obj,
    })


@appointments_required
def appointment_change_status(request, pk):
    obj = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid = [s[0] for s in Appointment.STATUS]
        if new_status in valid:
            obj.status = new_status
            obj.save(update_fields=["status"])
            log_action(request, "update", obj, description=f"تغییر وضعیت نوبت: {obj.get_status_display()}")
            messages.success(request, f"وضعیت به «{obj.get_status_display()}» تغییر کرد.")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "status": obj.status})
    return redirect(request.META.get("HTTP_REFERER", "secretary_dashboard"))


@appointments_required
def appointment_cancel(request, pk):
    obj = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        obj.status = "cancelled"
        obj.save(update_fields=["status"])
        log_action(request, "update", obj, description=f"لغو نوبت: {obj.patient.full_name}")
        messages.warning(request, "نوبت لغو شد.")
    return redirect(request.META.get("HTTP_REFERER", "secretary_dashboard"))


@appointments_required
def appointment_convert_to_visit(request, pk):
    from records.models import Visit
    from records.forms import VisitForm

    obj = get_object_or_404(Appointment, pk=pk)
    if obj.visit:
        messages.info(request, "این نوبت قبلاً به ویزیت تبدیل شده است.")
        return redirect("visit_detail", pk=obj.visit.pk)

    if request.method == "POST":
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = obj.patient
            visit.physician = obj.physician
            visit.save()
            obj.visit = visit
            obj.status = "in_progress"
            obj.save(update_fields=["visit", "status"])
            log_action(request, "create", visit, description=f"تبدیل نوبت به ویزیت")
            messages.success(request, "ویزیت ایجاد شد.")
            return redirect("visit_detail", pk=visit.pk)
    else:
        form = VisitForm(initial={"chief_complaint": obj.reason or ""})

    return render(request, "appointments/convert_form.html", {
        "form": form, "appointment": obj,
    })


@appointments_required
def patient_search_ajax(request):
    q = request.GET.get("q", "").strip()
    results = []
    if q and len(q) >= 2:
        patients = Patient.objects.filter(
            models.Q(first_name__icontains=q)
            | models.Q(last_name__icontains=q)
            | models.Q(mobile__icontains=q)
            | models.Q(national_code__icontains=q)
            | models.Q(file_number__icontains=q)
        )[:10]
        for p in patients:
            results.append({
                "id": p.pk, "name": p.full_name,
                "file_number": p.file_number, "mobile": p.mobile,
            })
    return JsonResponse({"results": results})


# ===== برنامه هفتگی =====

@medical_edit_required
def schedule_list(request):
    from accounts.models import User
    physicians = User.objects.filter(role__in=["physician", "manager"])
    schedules = WeeklySchedule.objects.select_related("physician").order_by(
        "physician", "day_of_week", "start_time"
    )
    return render(request, "appointments/schedule_list.html", {
        "schedules": schedules, "physicians": physicians,
    })


@medical_edit_required
def schedule_create(request):
    if request.method == "POST":
        form = WeeklyScheduleForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_action(request, "create", obj, description="افزودن برنامه هفتگی")
            messages.success(request, "برنامه ثبت شد.")
            return redirect("schedule_list")
    else:
        form = WeeklyScheduleForm()
    return render(request, "appointments/schedule_form.html", {"form": form, "title": "برنامه هفتگی جدید"})


@medical_edit_required
def schedule_edit(request, pk):
    obj = get_object_or_404(WeeklySchedule, pk=pk)
    if request.method == "POST":
        form = WeeklyScheduleForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("schedule_list")
    else:
        form = WeeklyScheduleForm(instance=obj)
    return render(request, "appointments/schedule_form.html", {"form": form, "title": "ویرایش برنامه"})


@medical_edit_required
def schedule_delete(request, pk):
    obj = get_object_or_404(WeeklySchedule, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "برنامه حذف شد.")
    return redirect("schedule_list")


# ===== مرخصی =====

@medical_edit_required
def timeoff_list(request):
    timeoffs = TimeOff.objects.select_related("physician").order_by("-date")
    return render(request, "appointments/timeoff_list.html", {"timeoffs": timeoffs})


@medical_edit_required
def timeoff_create(request):
    if request.method == "POST":
        form = TimeOffForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_action(request, "create", obj, description=f"ثبت مرخصی")
            messages.success(request, "مرخصی ثبت شد.")
            return redirect("timeoff_list")
    else:
        form = TimeOffForm()
    return render(request, "appointments/timeoff_form.html", {"form": form, "title": "مرخصی جدید"})


@medical_edit_required
def timeoff_delete(request, pk):
    obj = get_object_or_404(TimeOff, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "مرخصی حذف شد.")
    return redirect("timeoff_list")