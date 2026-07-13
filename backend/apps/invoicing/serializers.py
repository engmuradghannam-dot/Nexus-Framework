from rest_framework import serializers

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    creditable_remaining = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    outstanding = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["tax_amount", "total", "status", "created_at"]


class CreditNoteSerializer(serializers.ModelSerializer):
    return_type = serializers.CharField(read_only=True)
    original_invoice_number = serializers.CharField(source="original_invoice.invoice_number", read_only=True)
    original_invoice_type = serializers.CharField(source="original_invoice.invoice_type", read_only=True)

    class Meta:
        from .models import CreditNote
        model = CreditNote
        fields = "__all__"
        read_only_fields = ["tenant", "status", "total", "created_at"]
