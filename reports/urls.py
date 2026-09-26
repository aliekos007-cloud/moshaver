from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_dashboard, name="reports_dashboard"),
    path("consultants/", views.consultant_reports, name="consultant_reports"),
]