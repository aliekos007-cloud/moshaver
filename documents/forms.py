from django import forms
from .models import PatientDocument


class PatientDocumentForm(forms.ModelForm):
    class Meta:
        model = PatientDocument
        fields = ("visit", "document_type", "title", "file", "description")

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)
        if patient:
            self.fields["visit"].queryset = patient.visits.all()

        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault("rows", 2)
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.setdefault("class", "form-control")
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "form-select")
            else:
                w.attrs.setdefault("class", "form-control")

        self.fields["visit"].required = False
        self.fields["visit"].empty_label = "— بدون ارتباط با مراجعه —"