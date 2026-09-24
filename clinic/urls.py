from django.urls import path
from . import views

urlpatterns = [
    # تنظیمات
    path("settings/", views.clinic_settings, name="clinic_settings"),

    # اتاق‌ها
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/create/", views.room_create, name="room_create"),
    path("rooms/<int:pk>/edit/", views.room_edit, name="room_edit"),
    path("rooms/<int:pk>/toggle/", views.room_toggle, name="room_toggle"),
    path("rooms/<int:pk>/delete/", views.room_delete, name="room_delete"),
    path("rooms/reorder/", views.room_reorder, name="room_reorder"),
]