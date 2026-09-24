from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),

    # داشبورد منشی (زنده)
    path("secretary/dashboard/", views.secretary_dashboard, name="secretary_dashboard"),

    # مدیریت کاربران
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/password/", views.user_change_password, name="user_change_password"),

    # سطوح مشاور
    path("levels/", views.consultant_level_list, name="consultant_level_list"),
    path("levels/create/", views.consultant_level_create, name="consultant_level_create"),
    path("levels/<int:pk>/edit/", views.consultant_level_edit, name="consultant_level_edit"),
    path("levels/<int:pk>/toggle/", views.consultant_level_toggle, name="consultant_level_toggle"),
    path("levels/<int:pk>/delete/", views.consultant_level_delete, name="consultant_level_delete"),
]