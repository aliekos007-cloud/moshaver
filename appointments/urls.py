from django.urls import path
from . import views

urlpatterns = [
    # داشبورد منشی
    path("", views.secretary_dashboard, name="secretary_dashboard"),
    path("list/", views.appointment_list, name="appointment_list"),
    path("week/", views.appointment_week_view, name="appointment_week"),
    path("day/", views.appointment_day_view, name="appointment_day"),

    # ایجاد / ویرایش
    path("create/", views.appointment_create, name="appointment_create"),
    path("create/patient/<int:patient_pk>/", views.appointment_create, name="appointment_create_for_patient"),
    path("<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("<int:pk>/change-status/", views.appointment_change_status, name="appointment_change_status"),
    path("<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),
    path("<int:pk>/to-visit/", views.appointment_convert_to_visit, name="appointment_convert_to_visit"),

    # AJAX
    path("api/patient-search/", views.patient_search_ajax, name="patient_search_ajax"),

    # برنامه هفتگی
    path("schedules/", views.schedule_list, name="schedule_list"),
    path("schedules/create/", views.schedule_create, name="schedule_create"),
    path("schedules/<int:pk>/edit/", views.schedule_edit, name="schedule_edit"),
    path("schedules/<int:pk>/delete/", views.schedule_delete, name="schedule_delete"),

    # مرخصی
    path("timeoffs/", views.timeoff_list, name="timeoff_list"),
    path("timeoffs/create/", views.timeoff_create, name="timeoff_create"),
    path("timeoffs/<int:pk>/delete/", views.timeoff_delete, name="timeoff_delete"),
]