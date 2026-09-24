from django.urls import path
from . import views

urlpatterns = [
    path("", views.license_dashboard, name="license_dashboard"),
    path("create/", views.license_create, name="license_create"),
    path("<int:pk>/edit/", views.license_edit, name="license_edit"),
    path("<int:pk>/activate/", views.license_activate, name="license_activate"),
    path("<int:pk>/deactivate/", views.license_deactivate, name="license_deactivate"),
    path("<int:pk>/delete/", views.license_delete, name="license_delete"),
    path("enter-key/", views.license_enter_key, name="license_enter_key"),
    path("trial/", views.trial_status, name="trial_status"),
]