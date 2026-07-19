from rest_framework import serializers
from .models import (
    AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine,
    Invoice, InvoiceItem, Payment, FinancialReport
)

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = '__all__'

class ChartOfAccountsSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    account_type_category = serializers.CharField(source='account_type.category', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = ChartOfAccounts
        fields = '__all__'

class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = '__all__'

class JournalEntrySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    line_count = serializers.IntegerField(source='lines.count', read_only=True)
    is_balanced = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = '__all__'

    def get_is_balanced(self, obj):
        return obj.total_debit == obj.total_credit

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    payment_total = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'

    def get_payment_total(self, obj):
        return sum(p.amount for p in obj.payments.filter(status='completed'))

class PaymentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'

class FinancialReportSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)

    class Meta:
        model = FinancialReport
        fields = '__all__'
