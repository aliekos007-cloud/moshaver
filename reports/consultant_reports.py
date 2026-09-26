"""
گزارش‌های عملکرد مشاوران.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.models import User
from records.models import Session


def get_consultant_report(consultant, from_date=None, to_date=None):
    """
    گزارش عملکرد یک مشاور در بازهٔ مشخص.

    خروجی:
        {
            "total_sessions": int,
            "completed_sessions": int,
            "total_minutes": int,
            "total_revenue": Decimal,
            "by_day": [...],
        }
    """
    if to_date is None:
        to_date = timezone.localdate()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    qs = Session.objects.filter(
        consultant=consultant,
        scheduled_start__date__gte=from_date,
        scheduled_start__date__lte=to_date,
    )

    completed = qs.filter(status="completed")

    total_revenue = completed.aggregate(s=Sum("final_fee"))["s"] or Decimal(0)
    total_minutes = completed.aggregate(s=Sum("actual_duration_minutes"))["s"] or 0

    # گروه‌بندی روزانه
    by_day = {}
    for s in completed.order_by("scheduled_start"):
        day = s.scheduled_start.date()
        if day not in by_day:
            by_day[day] = {"count": 0, "minutes": 0, "revenue": Decimal(0)}
        by_day[day]["count"] += 1
        by_day[day]["minutes"] += s.actual_duration_minutes or 0
        by_day[day]["revenue"] += s.final_fee or Decimal(0)

    return {
        "consultant": consultant,
        "from_date": from_date,
        "to_date": to_date,
        "total_sessions": qs.count(),
        "completed_sessions": completed.count(),
        "total_minutes": total_minutes,
        "total_revenue": total_revenue,
        "by_day": sorted(by_day.items()),
    }


def get_all_consultants_summary(from_date=None, to_date=None):
    """گزارش خلاصه از همهٔ مشاوران."""
    if to_date is None:
        to_date = timezone.localdate()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    consultants = User.objects.filter(
        is_active=True,
        consultant_level__isnull=False,
    ).order_by("last_name", "first_name")

    result = []
    for c in consultants:
        report = get_consultant_report(c, from_date, to_date)
        result.append(report)

    return result