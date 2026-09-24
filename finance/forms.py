from datetime import date, datetime

from django import forms
import jdatetime

from .models import Transaction


class TransactionForm(forms.ModelForm):
    # فیلد تاریخ رو به‌صورت CharField تعریف می‌کنیم تا شمسی هم قبول کنه
    transaction_date = forms.CharField(
        label="تاریخ",
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_transaction_date"}),
    )

    class Meta:
        model = Transaction
        fields = (
            "transaction_type", "category", "amount",
            "transaction_date", "description",
            "patient", "visit",
        )

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)

        if patient:
            self.fields["patient"].initial = patient
            self.fields["visit"].queryset = patient.visits.all()

        self.fields["patient"].required = False
        self.fields["patient"].empty_label = "— بدون مراجع —"
        self.fields["visit"].required = False
        self.fields["visit"].empty_label = "— بدون مراجعه —"
        self.fields["transaction_type"].required = True
        self.fields["category"].required = True
        self.fields["amount"].required = True

        # دسته‌بندی‌ها
        self.fields["category"].choices = [("", "انتخاب دسته‌بندی...")] + Transaction.ALL_CATEGORIES

        # استایل
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.HiddenInput):
                continue
            w = field.widget
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault("rows", 2)
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "form-select")
            else:
                w.attrs.setdefault("class", "form-control")

    def clean_transaction_date(self):
        """پذیرش تاریخ به فرمت میلادی (2026-09-23) یا شمسی (1405/07/01)."""
        value = (self.cleaned_data.get("transaction_date") or "").strip()

        # اگه خالی بود → امروز
        if not value:
            return date.today()

        # میلادی: 2026-09-23
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass

        # شمسی: 1405/07/01
        try:
            parts = value.replace("-", "/").split("/")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                j = jdatetime.date(y, m, d)
                return j.togregorian()
        except Exception:
            pass

        # اگه هیچکدام → امروز
        return date.today()