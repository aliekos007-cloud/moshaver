from django.urls import path
from . import views

urlpatterns = [
    path("visit/new/<int:patient_pk>/", views.visit_create, name="visit_create"),
    path("visit/<int:pk>/", views.visit_detail, name="visit_detail"),
    path("visit/<int:pk>/print/", views.visit_print, name="visit_print"),
]