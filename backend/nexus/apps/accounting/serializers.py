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

    def validate(self, attrs):
        debit = attrs.get('debit', getattr(self.instance, 'debit', 0))
        credit = attrs.get('credit', getattr(self.instance, 'credit', 0))
        if debit and credit:
            raise serializers.ValidationError('A journal line cannot have both a debit and a credit amount')
        if not debit and not credit:
            raise serializers.ValidationError('A journal line must have a debit or a credit amount')
        return attrs

class JournalEntrySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    line_count = serializers.IntegerField(source='lines.count', read_only=True)
    is_balanced = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = '__all__'
        read_only_fields = ['entry_number']

    def get_is_balanced(self, obj):
        # SAP FI-style GL document balance check - sums the actual lines
        # rather than trusting the (possibly stale) header total fields.
        return obj.is_balanced

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
        read_only_fields = ['invoice_number', 'tax_amount', 'total', 'balance_due']

    def get_payment_total(self, obj):
        return sum(p.amount for p in obj.payments.filter(status='completed'))

    def validate(self, attrs):
        date = attrs.get('date', getattr(self.instance, 'date', None))
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        if date and due_date and due_date < date:
            raise serializers.ValidationError('Due date must be on or after the invoice date')
        return attrs

class PaymentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_number']

class FinancialReportSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)

    class Meta:
        model = FinancialReport
        fields = '__all__'

    def validate(self, attrs):
        period_start = attrs.get('period_start', getattr(self.instance, 'period_start', None))
        period_end = attrs.get('period_end', getattr(self.instance, 'period_end', None))
        if period_start and period_end and period_end < period_start:
            raise serializers.ValidationError('Period end must be on or after period start')
        return attrs
