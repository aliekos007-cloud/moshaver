from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ===== احراز هویت =====
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ===== داشبورد منشی =====
    path("secretary/dashboard/", views.secretary_dashboard, name="secretary_dashboard"),

    # ===== مدیریت کاربران =====
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/password/", views.user_change_password, name="user_change_password"),

    # ===== سطوح مشاور =====
    path("levels/", views.consultant_level_list, name="consultant_level_list"),
    path("levels/create/", views.consultant_level_create, name="consultant_level_create"),
    path("levels/<int:pk>/edit/", views.consultant_level_edit, name="consultant_level_edit"),
    path("levels/<int:pk>/toggle/", views.consultant_level_toggle, name="consultant_level_toggle"),
    path("levels/<int:pk>/delete/", views.consultant_level_delete, name="consultant_level_delete"),

    # ===== برنامه مشاوران =====
    path("consultants/", views.consultants_schedule_list, name="consultants_schedule_list"),
    path("consultants/<int:pk>/schedule/", views.consultant_weekly_schedule, name="consultant_weekly_schedule"),
    path("consultants/<int:pk>/month/", views.consultant_month_schedule, name="consultant_month_schedule"),

    # ===== API برنامه روز =====
    path("consultants/<int:pk>/day/save/", views.api_save_day_schedule, name="api_save_day_schedule"),
    path("consultants/<int:pk>/day/reset/", views.api_reset_day_schedule, name="api_reset_day_schedule"),

    # ===== مرخصی و استثناها =====
    path("consultants/<int:pk>/exceptions/", views.consultant_exceptions, name="consultant_exceptions"),
    path("consultants/<int:pk>/exceptions/create/", views.consultant_exception_create, name="consultant_exception_create"),
    path("consultants/<int:pk>/exceptions/<int:exc_id>/delete/", views.consultant_exception_delete, name="consultant_exception_delete"),

    # ===== جست‌وجوی نوبت =====
    path("slots/search/", views.slot_search, name="slot_search"),
    path("slots/<int:pk>/day/", views.api_day_slots, name="api_day_slots"),
]