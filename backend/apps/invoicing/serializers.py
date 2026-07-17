from rest_framework import serializers

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"
        read_only_fields = ["amount", "tax_amount"]


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceItemSerializer(many=True, read_only=True)
    creditable_remaining = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    outstanding = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    base_total = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    is_foreign = serializers.BooleanField(read_only=True)
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


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)

    class Meta:
        from .models import Payment
        model = Payment
        fields = "__all__"
        read_only_fields = ["tenant", "posted", "created_at"]
