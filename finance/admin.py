from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number", "transaction_type", "category",
        "amount", "transaction_date", "patient", "created_by",
    )
    list_filter = ("transaction_type", "category", "transaction_date")
    search_fields = ("receipt_number", "description", "patient__first_name", "patient__last_name")
    readonly_fields = ("receipt_number", "created_at")
    date_hierarchy = "transaction_date"