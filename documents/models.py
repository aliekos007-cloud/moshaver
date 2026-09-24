import os
from django.conf import settings
from django.db import models


class PatientDocument(models.Model):
    DOCUMENT_TYPES = [
        ("face_photo", "عکس صورت"),
        ("tongue_top", "عکس روی زبان"),
        ("tongue_bottom", "عکس زیر زبان"),
        ("ultrasound", "سونوگرافی"),
        ("lab", "آزمایش"),
        ("ct_scan", "CT Scan"),
        ("mri", "MRI"),
        ("ecg", "نوار قلب / ECG"),
        ("pdf", "فایل PDF"),
        ("other", "سایر مدارک"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE,
        related_name="documents", verbose_name="بیمار",
    )
    visit = models.ForeignKey(
        "records.Visit", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="documents",
        verbose_name="مراجعه مرتبط",
    )
    document_type = models.CharField("نوع مدرک", max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField("عنوان", max_length=200, blank=True)
    file = models.FileField("فایل", upload_to="patient_docs/%Y/%m/")
    description = models.TextField("توضیحات", blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name="ثبت‌کننده",
    )
    uploaded_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "مدرک بیمار"
        verbose_name_plural = "مدارک بیمار"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_document_type_display()}"

    @property
    def is_image(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]

    @property
    def is_pdf(self):
        return os.path.splitext(self.file.name)[1].lower() == ".pdf"

    @property
    def file_size_display(self):
        try:
            size = self.file.size
        except Exception:
            return "—"
        if size < 1024:
            return f"{size} بایت"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} کیلوبایت"
        return f"{size / (1024 * 1024):.1f} مگابایت"