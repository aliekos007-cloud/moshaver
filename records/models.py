from django.conf import settings
from django.db import models
from patients.models import Patient


class Visit(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE,
        related_name="visits", verbose_name="مراجع",
    )
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="طبیب",
    )
    visited_at = models.DateTimeField("تاریخ مراجعه", auto_now_add=True)

    prescription_serial = models.CharField(
        "شماره سریال نسخه", max_length=30, unique=True,
        blank=True, editable=False, null=True,
    )

    chief_complaint = models.TextField("علت مراجعه", blank=True)
    history = models.TextField("شرح حال", blank=True)
    brief_history = models.TextField("شرح مختصر مراجعی", blank=True)
    diagnosis = models.TextField("تشخیص", blank=True)
    treatment_plan = models.TextField("برنامه درمان", blank=True)
    follow_up = models.TextField("نتیجه پیگیری", blank=True)

    class Meta:
        verbose_name = "مراجعه"
        verbose_name_plural = "مراجعات"
        ordering = ["-visited_at"]
        indexes = [
            models.Index(fields=["patient", "-visited_at"], name="visit_patient_idx"),
            models.Index(fields=["physician", "-visited_at"], name="visit_physician_idx"),
            models.Index(fields=["-visited_at"], name="visit_date_idx"),
        ]

    def __str__(self):
        return f"{self.patient.full_name} — {self.visited_at:%Y/%m/%d}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.prescription_serial:
            import jdatetime
            today = jdatetime.date.today()
            year = str(today.year)
            count = Visit.objects.filter(
                prescription_serial__startswith=f"RX-{year}-"
            ).count() + 1
            serial = f"RX-{year}-{count:05d}"
            Visit.objects.filter(pk=self.pk).update(prescription_serial=serial)
            self.prescription_serial = serial