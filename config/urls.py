from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from accounts.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("records/", include("records.urls")),
    path("clinic/", include("clinic.urls")),
    path("documents/", include("documents.urls")),
    path("finance/", include("finance.urls")),
    path("core/", include("core.urls")),
    path("backup/", include("backup.urls")),
    path("audit/", include("audit.urls")),
    path("reports/", include("reports.urls")),
    path("licensing/", include("licensing.urls")),
    path("notifications/", include("notifications.urls")),   # ← این خط
    path("", dashboard, name="dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)