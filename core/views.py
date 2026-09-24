from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from patients.models import Patient
from records.models import Visit


@login_required
def global_search(request):
    q = (request.GET.get("q") or "").strip()
    results = {
        "patients": [],
        "visits": [],
    }

    if q:
        results["patients"] = list(
            Patient.objects.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(national_code__icontains=q)
                | Q(mobile__icontains=q)
                | Q(file_number__icontains=q)
            )[:20]
        )
        results["visits"] = list(
            Visit.objects.filter(
                Q(chief_complaint__icontains=q)
                | Q(diagnosis__icontains=q)
            )
            .select_related("patient", "physician")[:20]
        )

    return render(request, "core/search.html", {"q": q, "results": results})