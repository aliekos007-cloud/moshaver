"""مدیریت کاربران سامانه."""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..decorators import manager_required
from ..forms import UserCreateForm, UserEditForm, UserPasswordForm
from ..models import User
from audit.models import log_action


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