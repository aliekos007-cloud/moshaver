from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.clinic_settings, name="clinic_settings"),
]