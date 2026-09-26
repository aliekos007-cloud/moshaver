import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import (
    medical_view_required,
    medical_edit_required,
    timer_control_required,
    finance_edit_required,
)
from accounts.models import User
from audit.models import log_action
from patients.models import Patient
from clinic.models import ClinicSettings
from .models import Visit, Session, calculate_session_fee


# ==================================================
# ویوهای قدیمی Visit (برای سازگاری)
# ==================================================

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
    log_action(request, "print", visit, description="چاپ")
    return render(request, "records/visit_print.html", {
        "visit": visit,
        "clinic": clinic,
    })


# ==================================================
# لیست جلسات
# ==================================================

def session_list(request):
    """لیست جلسات — با فیلتر."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary", "consultant"):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    qs = Session.objects.select_related(
        "client", "consultant", "room"
    ).order_by("-scheduled_start")

    if role == "consultant":
        qs = qs.filter(consultant=request.user)

    date_filter = request.GET.get("date", "")
    if date_filter == "today":
        qs = qs.filter(scheduled_start__date=timezone.localdate())
    elif date_filter == "week":
        week_ago = timezone.localdate() - timedelta(days=7)
        qs = qs.filter(scheduled_start__date__gte=week_ago)
    elif date_filter == "month":
        month_ago = timezone.localdate() - timedelta(days=30)
        qs = qs.filter(scheduled_start__date__gte=month_ago)

    status_filter = request.GET.get("status", "")
    if status_filter:
        qs = qs.filter(status=status_filter)

    consultant_filter = request.GET.get("consultant", "")
    if consultant_filter and role in ("manager", "secretary"):
        qs = qs.filter(consultant_id=consultant_filter)

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(client__first_name__icontains=q)
            | Q(client__last_name__icontains=q)
            | Q(client__file_number__icontains=q)
            | Q(consultant__first_name__icontains=q)
            | Q(consultant__last_name__icontains=q)
        )

    total_count = qs.count()
    sessions = qs[:200]

    consultants = User.objects.filter(
        role="consultant", is_active=True,
    ).order_by("last_name", "first_name")

    return render(request, "records/session_list.html", {
        "sessions": sessions,
        "consultants": consultants,
        "date_filter": date_filter,
        "status_filter": status_filter,
        "consultant_filter": consultant_filter,
        "q": q,
        "total": total_count,
    })


# ==================================================
# ساخت جلسه
# ==================================================

def session_create(request):
    """ساخت جلسهٔ جدید."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary", "consultant"):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    from .forms import SessionCreateForm
    from patients.models import Patient
    from accounts.models import User

    # ===== پارامترهای URL =====
    client_id = request.GET.get("client")
    consultant_id = request.GET.get("consultant")
    date_str = request.GET.get("date")     # YYYY-MM-DD
    time_str = request.GET.get("time")     # HH:MM

    if request.method == "POST":
        form = SessionCreateForm(request.POST, current_user=request.user)
        if form.is_valid():
            session = form.save()
            session.created_by = request.user
            session.save(update_fields=["created_by"])

            log_action(
                request, "create_session", session,
                description=f"ساخت جلسه برای {session.client.full_name} با {session.consultant.get_full_name()}",
            )
            messages.success(
                request,
                f"جلسهٔ «{session.client.full_name}» با موفقیت ساخته شد."
            )
            return redirect("session_detail", pk=session.pk)
    else:
        initial = {}

        # مراجع
        if client_id:
            try:
                initial["client"] = Patient.objects.get(pk=client_id)
            except Patient.DoesNotExist:
                pass

        # مشاور
        if consultant_id:
            try:
                initial["consultant"] = User.objects.get(pk=consultant_id)
            except User.DoesNotExist:
                pass

        # تاریخ (میلادی از URL)
        if date_str:
            from datetime import datetime as dt
            try:
                initial["scheduled_date"] = dt.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        # ساعت
        if time_str:
            initial["scheduled_time"] = time_str

        form = SessionCreateForm(initial=initial, current_user=request.user)

    return render(request, "records/session_form.html", {
        "form": form,
    })

# ==================================================
# جزئیات جلسه
# ==================================================

def session_detail(request, pk):
    """جزئیات یک جلسه."""
    session = get_object_or_404(
        Session.objects.select_related("client", "consultant", "room"),
        pk=pk,
    )

    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role == "consultant" and session.consultant_id != request.user.id:
        messages.error(request, "دسترسی به این جلسه مجاز نیست.")
        return redirect("session_list")

    return render(request, "records/session_detail.html", {
        "session": session,
    })


# ==================================================
# شروع جلسه
# ==================================================

@timer_control_required
@require_POST
def session_start(request, pk):
    session = get_object_or_404(
        Session.objects.select_related("client", "consultant", "room"),
        pk=pk,
    )

    if session.status not in ("scheduled", "paused"):
        return JsonResponse({
            "ok": False,
            "error": "جلسه در وضعیت قابل شروع نیست."
        }, status=400)

    # ===== چک: مشاور در جلسهٔ فعال دیگری نباشد =====
    active_conflict = Session.objects.filter(
        consultant=session.consultant,
        status__in=["in_progress", "paused"],
    ).exclude(pk=session.pk).first()

    if active_conflict:
        return JsonResponse({
            "ok": False,
            "error": (
                f"«{session.consultant.get_full_name()}» در حال حاضر "
                f"در جلسهٔ دیگری با {active_conflict.client.full_name} است. "
                "ابتدا آن جلسه را ببندید."
            ),
        }, status=400)

    session.start(by_user=request.user)

    log_action(
        request, "start_session", session,
        description=f"شروع جلسهٔ {session.client.full_name}",
    )

    _update_presence_to_in_session(session)

    return JsonResponse({
        "ok": True,
        "session": _session_to_dict(session),
    })


# ==================================================
# وقفه و ادامه
# ==================================================

@timer_control_required
@require_POST
def session_pause(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.status != "in_progress":
        return JsonResponse({
            "ok": False,
            "error": "جلسه در حال اجرا نیست."
        }, status=400)

    session.pause(by_user=request.user)

    log_action(
        request, "pause_session", session,
        description=f"وقفه در جلسهٔ {session.client.full_name}",
    )

    return JsonResponse({"ok": True, "session": _session_to_dict(session)})


@timer_control_required
@require_POST
def session_resume(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.status != "paused":
        return JsonResponse({
            "ok": False,
            "error": "جلسه در وقفه نیست."
        }, status=400)

    session.resume(by_user=request.user)

    log_action(
        request, "resume_session", session,
        description=f"ادامهٔ جلسهٔ {session.client.full_name}",
    )

    return JsonResponse({"ok": True, "session": _session_to_dict(session)})


# ==================================================
# پایان جلسه
# ==================================================

@timer_control_required
@require_POST
def session_end(request, pk):
    session = get_object_or_404(
        Session.objects.select_related("client", "consultant", "room"),
        pk=pk,
    )

    if session.status not in ("in_progress", "paused"):
        return JsonResponse({
            "ok": False,
            "error": "جلسه در حال اجرا نیست."
        }, status=400)

    ended_at = None
    if request.POST.get("ended_at"):
        try:
            ended_at = timezone.make_aware(
                datetime.fromisoformat(request.POST["ended_at"])
            )
        except (ValueError, TypeError):
            pass

    session.end(by_user=request.user, ended_at=ended_at)

    log_action(
        request, "end_session", session,
        description=(
            f"پایان جلسهٔ {session.client.full_name} — "
            f"{session.actual_duration_minutes} دقیقه — "
            f"{session.final_fee:,.0f} تومان"
        ),
    )

    _update_presence_to_present(session)

    return JsonResponse({
        "ok": True,
        "session": _session_to_dict(session),
        "summary": {
            "duration_minutes": session.actual_duration_minutes,
            "calculated_fee": int(session.calculated_fee or 0),
            "discount_percent": session.discount_percent,
            "final_fee": int(session.final_fee or 0),
        }
    })


# ==================================================
# تمدید جلسه
# ==================================================

@timer_control_required
@require_POST
def session_extend(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.status not in ("in_progress", "paused"):
        return JsonResponse({
            "ok": False,
            "error": "جلسه در حال اجرا نیست."
        }, status=400)

    try:
        minutes = int(request.POST.get("minutes", 10))
    except (ValueError, TypeError):
        minutes = 10

    minutes = max(1, min(60, minutes))

    snapshot = dict(session.level_snapshot or {})
    snapshot["standard_minutes"] = snapshot.get("standard_minutes", 45) + minutes
    session.level_snapshot = snapshot
    session.extension_reason = request.POST.get("reason", "")[:200]
    session.save()

    log_action(
        request, "extend_session", session,
        description=f"تمدید {minutes} دقیقه‌ای جلسهٔ {session.client.full_name}",
    )

    return JsonResponse({
        "ok": True,
        "session": _session_to_dict(session),
        "extended_minutes": minutes,
    })


# ==================================================
# ثبت پرداخت
# ==================================================

@finance_edit_required
@require_POST
def session_pay(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.status != "awaiting_payment":
        return JsonResponse({
            "ok": False,
            "error": "جلسه در وضعیت انتظار پرداخت نیست."
        }, status=400)

    try:
        amount = int(request.POST.get("amount", 0))
    except (ValueError, TypeError):
        amount = 0

    method = request.POST.get("method", "cash")
    note = request.POST.get("note", "")[:300]

    if amount <= 0:
        return JsonResponse({
            "ok": False,
            "error": "مبلغ پرداخت باید بزرگ‌تر از صفر باشد."
        }, status=400)

    session.register_payment(
        amount=amount,
        method=method,
        by_user=request.user,
        note=note,
    )

    _create_transaction(session, amount, method, request.user)

    log_action(
        request, "register_payment", session,
        description=f"ثبت پرداخت {amount:,} تومان برای جلسهٔ {session.client.full_name}",
    )

    return JsonResponse({
        "ok": True,
        "session": _session_to_dict(session),
        "paid": {
            "amount": amount,
            "method": method,
            "remaining": int(session.remaining_amount or 0),
            "status": session.payment_status,
        }
    })


# ==================================================
# نسیه
# ==================================================

@finance_edit_required
@require_POST
def session_defer(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.status != "awaiting_payment":
        return JsonResponse({
            "ok": False,
            "error": "جلسه در وضعیت انتظار پرداخت نیست."
        }, status=400)

    note = request.POST.get("note", "")[:300]

    session.defer_payment(by_user=request.user, note=note)

    _add_client_debt(session.client, session.final_fee or 0)

    log_action(
        request, "defer_payment", session,
        description=f"نسیه: {session.final_fee:,} تومان برای {session.client.full_name}",
    )

    return JsonResponse({
        "ok": True,
        "session": _session_to_dict(session),
    })


# ==================================================
# ابزارهای کمکی
# ==================================================

def _session_to_dict(session):
    return {
        "id": session.id,
        "status": session.status,
        "status_display": session.get_status_display(),
        "payment_status": session.payment_status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "elapsed_seconds": session.elapsed_seconds(),
        "remaining_seconds": session.remaining_seconds(),
        "current_fee": int(session.current_fee() or 0),
        "calculated_fee": int(session.calculated_fee or 0),
        "final_fee": int(session.final_fee or 0),
        "actual_duration_minutes": session.actual_duration_minutes,
        "total_paused_seconds": session.total_paused_seconds,
    }


def _update_presence_to_in_session(session):
    from clinic.models import ConsultantDailyPresence
    today = timezone.localdate()
    ConsultantDailyPresence.objects.filter(
        consultant=session.consultant,
        date=today,
    ).update(status="in_session")


def _update_presence_to_present(session):
    from clinic.models import ConsultantDailyPresence
    today = timezone.localdate()
    ConsultantDailyPresence.objects.filter(
        consultant=session.consultant,
        date=today,
        status="in_session",
    ).update(status="present")


def _create_transaction(session, amount, method, user):
    try:
        from finance.models import Transaction
        Transaction.objects.create(
            transaction_type="income",
            amount=amount,
            description=(
                f"درآمد جلسه — {session.client.full_name} "
                f"با {session.consultant.get_full_name()}"
            ),
            transaction_date=timezone.localdate(),
            patient=session.client,
        )
    except Exception:
        pass


def _add_client_debt(client, amount):
    if amount <= 0:
        return
    client.outstanding_balance = (client.outstanding_balance or 0) + amount
    client.save(update_fields=["outstanding_balance"])

# ==================================================
# ویرایش جلسه
# ==================================================

def session_edit(request, pk):
    """ویرایش جلسه — فقط در وضعیت scheduled یا paused."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary", "consultant"):
        messages.error(request, "دسترسی مجاز نیست.")
        return redirect("dashboard")

    session = get_object_or_404(
        Session.objects.select_related("client", "consultant", "room"),
        pk=pk,
    )

    # مشاور فقط جلسات خودش
    if role == "consultant" and session.consultant_id != request.user.id:
        messages.error(request, "دسترسی به این جلسه مجاز نیست.")
        return redirect("session_list")

    # چک وضعیت
    if session.status not in ("scheduled", "paused"):
        messages.error(
            request,
            f"این جلسه در وضعیت «{session.get_status_display()}» است و قابل ویرایش نیست. "
            "فقط جلسات زمان‌بندی‌شده یا در وقفه قابل ویرایش هستند."
        )
        return redirect("session_detail", pk=session.pk)

    from .forms import SessionEditForm

    if request.method == "POST":
        form = SessionEditForm(request.POST, instance=session)
        if form.is_valid():
            form.save()

            log_action(
                request, "update_session", session,
                description=f"ویرایش جلسهٔ {session.client.full_name}",
            )
            messages.success(request, "جلسه با موفقیت ویرایش شد.")
            return redirect("session_detail", pk=session.pk)
    else:
        # مقدار اولیه از خود جلسه
        form = SessionEditForm(instance=session)

    return render(request, "records/session_edit_form.html", {
        "form": form,
        "session": session,
    })


# ==================================================
# حذف جلسه (لغو)
# ==================================================

@require_POST
def session_delete(request, pk):
    """لغو جلسه — فقط جلسات زمان‌بندی‌شده."""
    if not request.user.is_authenticated:
        return redirect("login")

    role = getattr(request.user, "role", None)
    if role not in ("manager", "secretary"):
        messages.error(request, "فقط مدیر و منشی می‌توانند جلسه را لغو کنند.")
        return redirect("dashboard")

    session = get_object_or_404(Session, pk=pk)

    if session.status not in ("scheduled", "paused"):
        messages.error(
            request,
            "فقط جلسات زمان‌بندی‌شده یا در وقفه قابل لغو هستند."
        )
        return redirect("session_detail", pk=session.pk)

    client_name = session.client.full_name
    session.status = "cancelled"
    session.save(update_fields=["status"])

    log_action(
        request, "cancel_session", session,
        description=f"لغو جلسهٔ {client_name}",
    )
    messages.success(request, f"جلسهٔ «{client_name}» لغو شد.")
    return redirect("session_list")