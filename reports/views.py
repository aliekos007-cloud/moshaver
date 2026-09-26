from licensing.decorators import feature_required
import csv
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
import jdatetime

from accounts import permissions
from audit.models import log_action
from .services import (
    get_period_range, compute_stats, get_daily_chart,
    get_top_patients, get_top_medicines,
    get_income_by_category, get_expense_by_category,
)


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

@feature_required("reports")
@login_required
def reports_dashboard(request):
    if not permissions.is_manager(request.user) and not permissions.can_view_medical(request.user):
        raise PermissionDenied("دسترسی به گزارش‌ها مجاز نیست.")

    period = request.GET.get("period", "month")
    date_from_s = request.GET.get("from", "")
    date_to_s = request.GET.get("to", "")

    date_from, date_to = get_period_range(period, _parse_date(date_from_s), _parse_date(date_to_s))

    stats = compute_stats(date_from, date_to)
    visits_chart = get_daily_chart(date_from, date_to, metric="visits")
    finance_chart = get_daily_chart(date_from, date_to, metric="income")
    top_patients = get_top_patients(date_from, date_to)
    top_medicines = get_top_medicines(date_from, date_to)
    income_cats = get_income_by_category(date_from, date_to)
    expense_cats = get_expense_by_category(date_from, date_to)

    # تبدیل ماه شمسی به نام
    j_from = jdatetime.date.fromgregorian(date=date_from)
    j_to = jdatetime.date.fromgregorian(date=date_to)

    return render(request, "reports/dashboard.html", {
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "date_from_s": date_from.isoformat(),
        "date_to_s": date_to.isoformat(),
        "j_from": j_from,
        "j_to": j_to,
        "stats": stats,
        "visits_chart": visits_chart,
        "finance_chart": finance_chart,
        "top_patients": top_patients,
        "top_medicines": top_medicines,
        "income_cats": income_cats,
        "expense_cats": expense_cats,
    })


@feature_required("reports")
@login_required
def reports_export_csv(request):
    if not permissions.is_manager(request.user):
        raise PermissionDenied

    period = request.GET.get("period", "month")
    date_from_s = request.GET.get("from", "")
    date_to_s = request.GET.get("to", "")
    date_from, date_to = get_period_range(period, _parse_date(date_from_s), _parse_date(date_to_s))

    stats = compute_stats(date_from, date_to)

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="report_{date_from}_{date_to}.csv"'

    response.write("\ufeff")  # BOM برای Excel فارسی
    writer = csv.writer(response)
    writer.writerow(["گزارش مدیریتی سامانه طبیب"])
    writer.writerow([f"از {date_from} تا {date_to}"])
    writer.writerow([])
    writer.writerow(["شاخص", "مقدار"])
    writer.writerow(["تعداد کل مراجعین", stats["total_patients"]])
    writer.writerow(["مراجعین جدید در بازه", stats["new_patients"]])
    writer.writerow(["کل مراجعات", stats["total_visits"]])
    writer.writerow(["مراجعین مراجعه‌کننده (یکتا)", stats["unique_patients_visited"]])
    writer.writerow(["اعمال یداوی", stats["manual_count"]])
    writer.writerow(["بازتاب‌درمانی", stats["reflex_count"]])
    writer.writerow(["دیسکوپاتی", stats["discopathy_count"]])
    writer.writerow(["مدارک آپلودشده", stats["docs_count"]])
    writer.writerow(["رضایت‌نامه‌ها", stats["consents_count"]])
    writer.writerow(["کالاهای کم‌موجود", stats["low_stock"]])
    writer.writerow([])
    writer.writerow(["جمع درآمد (تومان)", int(stats["income"])])
    writer.writerow(["جمع هزینه (تومان)", int(stats["expense"])])
    writer.writerow(["مانده (تومان)", int(stats["balance"])])
    writer.writerow(["تعداد تراکنش‌ها", stats["tx_count"]])

    log_action(request, "export", description="خروجی CSV گزارش‌ها")
    return response

# ==================================================
# گزارش مشاوران
# ==================================================

def consultant_reports(request):
    """گزارش عملکرد مشاوران."""
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import User
    from .consultant_reports import get_all_consultants_summary, get_consultant_report

    # فیلتر بازه
    days = int(request.GET.get("days", 30))
    to_date = timezone.localdate()
    from_date = to_date - timedelta(days=days)

    # فیلتر مشاور
    consultant_id = request.GET.get("consultant")

    if consultant_id:
        consultant = User.objects.get(pk=consultant_id)
        report = get_consultant_report(consultant, from_date, to_date)
        reports = [report]
    else:
        reports = get_all_consultants_summary(from_date, to_date)

    # لیست مشاوران برای dropdown
    consultants = User.objects.filter(
        is_active=True, consultant_level__isnull=False,
    ).order_by("last_name", "first_name")

    # آمار کلی
    total_sessions = sum(r["completed_sessions"] for r in reports)
    total_minutes = sum(r["total_minutes"] for r in reports)
    total_revenue = sum(r["total_revenue"] for r in reports)

    return render(request, "reports/consultant_reports.html", {
        "reports": reports,
        "consultants": consultants,
        "days": days,
        "from_date": from_date,
        "to_date": to_date,
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_revenue": total_revenue,
    })