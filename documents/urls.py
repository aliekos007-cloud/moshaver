from django.urls import path
from . import views

urlpatterns = [
    path("upload/<int:patient_pk>/", views.document_upload, name="document_upload"),
    path("<int:pk>/delete/", views.document_delete, name="document_delete"),
]