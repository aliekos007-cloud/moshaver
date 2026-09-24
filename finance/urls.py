from django.urls import path
from . import views

urlpatterns = [
    path("", views.finance_dashboard, name="finance_dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/new/", views.transaction_create, name="transaction_create"),
    path("transactions/new/<int:patient_pk>/", views.transaction_create, name="transaction_create_for_patient"),
    path("transactions/<int:pk>/", views.transaction_detail, name="transaction_detail"),
    path("transactions/<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
    path("transactions/<int:pk>/receipt/", views.receipt_print, name="receipt_print"),
]