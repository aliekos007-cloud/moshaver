from datetime import date
from django.conf import settings
from django.db import models


class Transaction(models.Model):
    """هر تراکنش مالی — درآمد یا هزینه."""

    TYPE = [
        ("income", "درآمد"),
        ("expense", "هزینه"),
    ]

    INCOME_CATEGORIES = [
        ("visit_fee", "ویزیت"),
        ("service", "خدمات"),
        ("product_sale", "فروش اقلام"),
        ("other_income", "سایر درآمدها"),
    ]

    EXPENSE_CATEGORIES = [
        ("purchase", "خرید"),
        ("rent", "اجاره"),
        ("salary", "حقوق"),
        ("equipment", "تجهیزات"),
        ("current_expense", "هزینه جاری"),
        ("other_expense", "سایر هزینه‌ها"),
    ]

    ALL_CATEGORIES = INCOME_CATEGORIES + EXPENSE_CATEGORIES

    receipt_number = models.CharField(
        "شماره رسید", max_length=30, unique=True,
        blank=True, editable=False, null=True,
    )
    transaction_type = models.CharField("نوع تراکنش", max_length=10, choices=TYPE)
    category = models.CharField("دسته‌بندی", max_length=30, choices=ALL_CATEGORIES)
    amount = models.DecimalField("مبلغ (تومان)", max_digits=14, decimal_places=0)
    transaction_date = models.DateField("تاریخ", default=date.today)
    description = models.TextField("توضیحات", blank=True)

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions",
        verbose_name="بیمار",
    )
    visit = models.ForeignKey(
        "records.Visit", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions",
        verbose_name="مراجعه مرتبط",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["-transaction_date"], name="tx_date_idx"),
            models.Index(fields=["transaction_type", "-transaction_date"], name="tx_type_date_idx"),
            models.Index(fields=["category"], name="tx_category_idx"),
            models.Index(fields=["patient"], name="tx_patient_idx"),
        ]

    def __str__(self):
        sign = "+" if self.transaction_type == "income" else "-"
        return f"{sign} {self.amount:,} — {self.get_category_display()}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.receipt_number:
            import jdatetime
            today = jdatetime.date.today()
            year = str(today.year)
            prefix = "RC" if self.transaction_type == "income" else "PY"
            count = Transaction.objects.filter(
                receipt_number__startswith=f"{prefix}-{year}-"
            ).count() + 1
            number = f"{prefix}-{year}-{count:05d}"
            Transaction.objects.filter(pk=self.pk).update(receipt_number=number)
            self.receipt_number = number