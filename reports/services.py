"""سرویس محاسبات گزارش‌ها."""
from datetime import date, timedelta
from decimal import Decimal

import jdatetime
from django.db.models import Sum, Count, Q
from django.utils import timezone


def get_period_range(period, date_from=None, date_to=None):
    """بازه‌ی تاریخ بر اساس انتخاب کاربر."""
    today = date.today()
    if period == "today":
        return today, today
    if period == "week":
        start = today - timedelta(days=6)
        return start, today
    if period == "month":
        # ماه شمسی جاری
        jtoday = jdatetime.date.today()
        first_j = jdatetime.date(jtoday.year, jtoday.month, 1)
        first_g = first_j.togregorian()
        return first_g, today
    if period == "year":
        jtoday = jdatetime.date.today()
        first_j = jdatetime.date(jtoday.year, 1, 1)
        first_g = first_j.togregorian()
        return first_g, today
    if period == "custom" and date_from and date_to:
        return date_from, date_to
    # پیش‌فرض: این ماه شمسی
    jtoday = jdatetime.date.today()
    first_j = jdatetime.date(jtoday.year, jtoday.month, 1)
    return first_j.togregorian(), today


def compute_stats(date_from, date_to):
    """آمار کلی در بازه."""
    from patients.models import Patient
    from records.models import Visit
    from finance.models import Transaction
    from therapies.models import ManualTherapy, ReflexTherapy, Discopathy
    from documents.models import PatientDocument
    from consent.models import PatientConsent
    from inventory.models import Item

    # === بیماران ===
    new_patients = Patient.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to).count()
    total_patients = Patient.objects.count()

    # === مراجعات ===
    visits_qs = Visit.objects.filter(visited_at__date__gte=date_from, visited_at__date__lte=date_to)
    total_visits = visits_qs.count()
    unique_patients_visited = visits_qs.values("patient").distinct().count()

    # === درمان‌ها ===
    manual_count = ManualTherapy.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to).count()
    reflex_count = ReflexTherapy.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to).count()
    discopathy_count = Discopathy.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to).count()

    # === مالی ===
    txs = Transaction.objects.filter(transaction_date__gte=date_from, transaction_date__lte=date_to)
    income = txs.filter(transaction_type="income").aggregate(s=Sum("amount"))["s"] or Decimal(0)
    expense = txs.filter(transaction_type="expense").aggregate(s=Sum("amount"))["s"] or Decimal(0)
    balance = income - expense
    tx_count = txs.count()

    # === مدارک و رضایت‌نامه ===
    docs_count = PatientDocument.objects.filter(uploaded_at__date__gte=date_from, uploaded_at__date__lte=date_to).count()
    consents_count = PatientConsent.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to).count()

    # === انبار ===
    low_stock = 0
    for item in Item.objects.filter(is_active=True):
        if item.is_low:
            low_stock += 1

    return {
        "new_patients": new_patients,
        "total_patients": total_patients,
        "total_visits": total_visits,
        "unique_patients_visited": unique_patients_visited,
        "manual_count": manual_count,
        "reflex_count": reflex_count,
        "discopathy_count": discopathy_count,
        "income": income,
        "expense": expense,
        "balance": balance,
        "tx_count": tx_count,
        "docs_count": docs_count,
        "consents_count": consents_count,
        "low_stock": low_stock,
    }


def get_daily_chart(date_from, date_to, metric="visits"):
    """داده‌ی نمودار روزانه."""
    from records.models import Visit
    from finance.models import Transaction

    days = (date_to - date_from).days + 1
    if days > 60:
        # اگه بازه طولانیه، هفتگی گروه‌بندی کن
        step = max(1, days // 30)
    else:
        step = 1

    labels = []
    data_1 = []
    data_2 = []

    d = date_from
    while d <= date_to:
        jd = jdatetime.date.fromgregorian(date=d)
        labels.append(jd.strftime("%m/%d"))

        if metric == "visits":
            data_1.append(Visit.objects.filter(visited_at__date=d).count())
            data_2.append(0)
        elif metric == "income":
            inc = Transaction.objects.filter(
                transaction_date=d, transaction_type="income"
            ).aggregate(s=Sum("amount"))["s"] or 0
            exp = Transaction.objects.filter(
                transaction_date=d, transaction_type="expense"
            ).aggregate(s=Sum("amount"))["s"] or 0
            data_1.append(int(inc))
            data_2.append(int(exp))

        d += timedelta(days=step)

    return {"labels": labels, "data_1": data_1, "data_2": data_2}


def get_top_patients(date_from, date_to, limit=10):
    """بیماران با بیشترین مراجعه در بازه."""
    from records.models import Visit
    return (
        Visit.objects
        .filter(visited_at__date__gte=date_from, visited_at__date__lte=date_to)
        .values("patient__id", "patient__first_name", "patient__last_name", "patient__file_number")
        .annotate(visit_count=Count("id"))
        .order_by("-visit_count")[:limit]
    )


def get_top_medicines(date_from, date_to, limit=10):
    """داروهای بیشترین تجویز در بازه."""
    from records.models import PrescriptionItem
    return (
        PrescriptionItem.objects
        .filter(visit__visited_at__date__gte=date_from, visit__visited_at__date__lte=date_to)
        .values("medicine__name")
        .annotate(prescription_count=Count("id"))
        .order_by("-prescription_count")[:limit]
    )


def get_income_by_category(date_from, date_to):
    """درآمد به تفکیک دسته."""
    from finance.models import Transaction
    return (
        Transaction.objects
        .filter(
            transaction_type="income",
            transaction_date__gte=date_from,
            transaction_date__lte=date_to,
        )
        .values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )


def get_expense_by_category(date_from, date_to):
    """هزینه به تفکیک دسته."""
    from finance.models import Transaction
    return (
        Transaction.objects
        .filter(
            transaction_type="expense",
            transaction_date__gte=date_from,
            transaction_date__lte=date_to,
        )
        .values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )