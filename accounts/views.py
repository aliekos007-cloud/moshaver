from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from audit.models import log_action
from .decorators import manager_required
from .forms import UserCreateForm, UserEditForm, UserPasswordForm
from .models import User


@login_required
def dashboard(request):
    from patients.models import Patient
    from records.models import Visit
    from finance.models import Transaction
    from decimal import Decimal
    from django.db.models import Sum

    today = timezone.now().date()

    patient_count = Patient.objects.count()
    today_visits = Visit.objects.filter(visited_at__date=today).count()
    total_visits = Visit.objects.count()

    today_income = Transaction.objects.filter(
        transaction_date=today, transaction_type="income"
    ).aggregate(s=Sum("amount"))["s"] or Decimal(0)
    today_expense = Transaction.objects.filter(
        transaction_date=today, transaction_type="expense"
    ).aggregate(s=Sum("amount"))["s"] or Decimal(0)

    recent_patients = Patient.objects.all()[:5]
    recent_visits = Visit.objects.select_related("patient", "physician")[:5]

    return render(request, "dashboard.html", {
        "patient_count": patient_count,
        "today_visits": today_visits,
        "total_visits": total_visits,
        "today_income": today_income,
        "today_expense": today_expense,
        "recent_patients": recent_patients,
        "recent_visits": recent_visits,
    })


def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ===== مدیریت کاربران =====

@manager_required
def user_list(request):
    users = User.objects.all().order_by("-is_active", "last_name", "first_name")
    return render(request, "accounts/user_list.html", {"users": users})


@manager_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(
                request, "create", user,
                description=f"ساخت کاربر جدید: {user.get_full_name()} ({user.get_role_display()})",
            )
            messages.success(request, f"کاربر «{user.get_full_name()}» با موفقیت ساخته شد.")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "کاربر جدید",
    })


@manager_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)

    is_self = (user.pk == request.user.pk)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            obj = form.save(commit=False)
            if is_self:
                obj.role = user.role
                obj.is_active = True
            obj.save()
            log_action(
                request, "update", user,
                description=f"ویرایش کاربر: {user.get_full_name()}",
            )
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": f"ویرایش {user.get_full_name()}",
        "edit_user": user,
        "is_self": is_self,
    })


@manager_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if user.pk == request.user.pk:
            messages.error(request, "نمی‌توانید حساب خودتان را غیرفعال کنید.")
        else:
            user.is_active = not user.is_active
            user.save()
            status = "فعال" if user.is_active else "غیرفعال"
            log_action(
                request, "update", user,
                description=f"تغییر وضعیت کاربر: {user.get_full_name()} → {status}",
            )
            messages.success(request, f"کاربر {user.get_full_name()} {status} شد.")
    return redirect("user_list")


@manager_required
def user_change_password(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.save()
            log_action(
                request, "update", user,
                description=f"تغییر رمز عبور کاربر: {user.get_full_name()}",
            )
            messages.success(request, f"رمز عبور {user.get_full_name()} با موفقیت تغییر کرد.")
            return redirect("user_list")
    else:
        form = UserPasswordForm()

    return render(request, "accounts/user_password.html", {
        "form": form,
        "edit_user": user,
    })