from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_dashboard, name="reports_dashboard"),
    path("export/csv/", views.reports_export_csv, name="reports_export_csv"),
]