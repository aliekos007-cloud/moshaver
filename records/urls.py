from django.urls import path
from . import views

urlpatterns = [
    # ===== جلسات =====
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/create/", views.session_create, name="session_create"),
    path("sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path("sessions/<int:pk>/edit/", views.session_edit, name="session_edit"),
    path("sessions/<int:pk>/delete/", views.session_delete, name="session_delete"),

    # ===== API جلسه =====
    path("session/<int:pk>/start/", views.session_start, name="session_start"),
    path("session/<int:pk>/pause/", views.session_pause, name="session_pause"),
    path("session/<int:pk>/resume/", views.session_resume, name="session_resume"),
    path("session/<int:pk>/end/", views.session_end, name="session_end"),
    path("session/<int:pk>/extend/", views.session_extend, name="session_extend"),
    path("session/<int:pk>/pay/", views.session_pay, name="session_pay"),
    path("session/<int:pk>/defer/", views.session_defer, name="session_defer"),
]