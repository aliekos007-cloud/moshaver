from django.urls import path
from . import views

urlpatterns = [
    path("api/list/", views.api_list, name="notifications_api_list"),
    path("api/unread/", views.api_unread_count, name="notifications_api_unread"),
    path("api/<int:pk>/read/", views.api_mark_read, name="notifications_api_read"),
    path("api/mark-all-read/", views.api_mark_all_read, name="notifications_api_mark_all"),
    path("", views.notification_list, name="notifications_list"),
]