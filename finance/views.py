from licensing.decorators import feature_required
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import finance_view_required, finance_edit_required
from audit.models import log_action
from patients.models import Patient
from clinic.models import ClinicSettings
from .models import Transaction
from .forms import TransactionForm


def _stats(queryset):
    income = queryset.filter(transaction_type="income").aggregate(s=Sum("amount"))["s"] or Decimal(0)
    expense = queryset.filter(transaction_type="expense").aggregate(s=Sum("amount"))["s"] or Decimal(0)
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "count": queryset.count(),
    }

@feature_required("finance")
@finance_view_required
def finance_dashboard(request):
    today = date.today()
    first_of_month = today.replace(day=1)

    all_qs = Transaction.objects.all()
    today_qs = all_qs.filter(transaction_date=today)
    month_qs = all_qs.filter(transaction_date__gte=first_of_month)

    recent = all_qs.select_related("patient", "created_by")[:10]

    chart_days = []
    chart_income = []
    chart_expense = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        income = all_qs.filter(transaction_date=d, transaction_type="income").aggregate(s=Sum("amount"))["s"] or 0
        expense = all_qs.filter(transaction_date=d, transaction_type="expense").aggregate(s=Sum("amount"))["s"] or 0
        import jdatetime
        jd = jdatetime.date.fromgregorian(date=d)
        chart_days.append(jd.strftime("%m/%d"))
        chart_income.append(int(income))
        chart_expense.append(int(expense))

    return render(request, "finance/dashboard.html", {
        "today_stats": _stats(today_qs),
        "month_stats": _stats(month_qs),
        "all_stats": _stats(all_qs),
        "recent": recent,
        "chart_days": chart_days,
        "chart_income": chart_income,
        "chart_expense": chart_expense,
    })

@feature_required("finance")
@finance_view_required
def transaction_list(request):
    qs = Transaction.objects.select_related("patient", "created_by")

    t_type = request.GET.get("type", "")
    category = request.GET.get("category", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    q = request.GET.get("q", "").strip()

    if t_type in ("income", "expense"):
        qs = qs.filter(transaction_type=t_type)
    if category:
        qs = qs.filter(category=category)
    if date_from:
        qs = qs.filter(transaction_date__gte=date_from)
    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)
    if q:
        qs = qs.filter(
            Q(receipt_number__icontains=q)
            | Q(description__icontains=q)
            | Q(patient__first_name__icontains=q)
            | Q(patient__last_name__icontains=q)
        )

    stats = _stats(qs)
    return render(request, "finance/list.html", {
        "transactions": qs,
        "stats": stats,
        "type_filter": t_type,
        "category_filter": category,
        "from_filter": date_from,
        "to_filter": date_to,
        "q": q,
        "categories": Transaction.ALL_CATEGORIES,
    })


@feature_required("finance")
@finance_edit_required
def transaction_create(request, patient_pk=None):
    patient = None
    if patient_pk:
        patient = get_object_or_404(Patient, pk=patient_pk)

    if request.method == "POST":
        form = TransactionForm(request.POST, patient=patient)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            log_action(request, "create", obj, description=f"ثبت تراکنش: {obj.get_category_display()}")
            messages.success(request, "تراکنش با موفقیت ثبت شد.")
            return redirect("transaction_detail", pk=obj.pk)
    else:
        form = TransactionForm(patient=patient)

    return render(request, "finance/form.html", {
        "form": form,
        "patient": patient,
    })


@feature_required("finance")
@finance_view_required
def transaction_detail(request, pk):
    obj = get_object_or_404(
        Transaction.objects.select_related("patient", "visit", "created_by"), pk=pk,
    )
    return render(request, "finance/detail.html", {"tx": obj})


@feature_required("finance")
@finance_edit_required
def transaction_delete(request, pk):
    obj = get_object_or_404(Transaction, pk=pk)
    if request.method == "POST":
        log_action(request, "delete", obj, description=f"حذف تراکنش: {obj.receipt_number}")
        obj.delete()
        messages.success(request, "تراکنش حذف شد.")
    return redirect("transaction_list")


@feature_required("finance")
@finance_view_required
def receipt_print(request, pk):
    obj = get_object_or_404(
        Transaction.objects.select_related("patient", "visit", "created_by"), pk=pk,
    )
    clinic = ClinicSettings.get()
    log_action(request, "print", obj, description=f"چاپ رسید: {obj.receipt_number}")
    return render(request, "finance/receipt_print.html", {
        "tx": obj,
        "clinic": clinic,
    })