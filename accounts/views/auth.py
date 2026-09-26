"""توابع احراز هویت و خروج."""
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


def logout_view(request):
    """خروج از حساب کاربری."""
    auth_logout(request)
    return redirect("login")