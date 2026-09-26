from django.urls import path
from . import views

urlpatterns = [
    # API
    path("api/consultant-room/<int:consultant_id>/", views.api_consultant_room, name="api_consultant_room"),
    
    # تنظیمات
    path("settings/", views.clinic_settings, name="clinic_settings"),

    # اتاق‌ها
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/create/", views.room_create, name="room_create"),
    path("rooms/<int:pk>/edit/", views.room_edit, name="room_edit"),
    path("rooms/<int:pk>/toggle/", views.room_toggle, name="room_toggle"),
    path("rooms/<int:pk>/delete/", views.room_delete, name="room_delete"),
    path("rooms/reorder/", views.room_reorder, name="room_reorder"),

    # حضور مشاور
    path("presence/", views.presence_list, name="presence_list"),
    path("presence/register/", views.presence_register, name="presence_register"),
    path("presence/<int:pk>/change-room/", views.presence_change_room, name="presence_change_room"),
    path("presence/<int:pk>/checkout/", views.presence_checkout, name="presence_checkout"),
    path("presence/<int:pk>/toggle-break/", views.presence_toggle_break, name="presence_toggle_break"),
    
    # API
    path("api/consultant-room/<int:consultant_id>/", views.api_consultant_room, name="api_consultant_room"),
    path("api/slots/<int:consultant_id>/", views.api_consultant_slots, name="api_consultant_slots"),
    path("api/nearest/<int:consultant_id>/", views.api_nearest_slot, name="api_nearest_slot"),
    path("api/summary/<int:consultant_id>/", views.api_days_summary, name="api_days_summary"),
]