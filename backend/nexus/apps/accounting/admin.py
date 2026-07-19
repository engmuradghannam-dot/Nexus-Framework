from django.contrib import admin
from .models import (
    AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine,
    Invoice, InvoiceItem, Payment, FinancialReport
)

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category']
    list_filter = ['category']

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'account_type', 'current_balance', 'is_active']
    list_filter = ['account_type', 'is_active', 'company']
    search_fields = ['code', 'name']

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'company', 'date', 'status', 'total_debit', 'total_credit']
    list_filter = ['status', 'date']
    search_fields = ['entry_number', 'description']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'invoice_type', 'customer_name', 'total', 'status', 'date']
    list_filter = ['invoice_type', 'status', 'date']
    search_fields = ['invoice_number', 'customer_name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'amount', 'method', 'status', 'date']
    list_filter = ['method', 'status', 'date']

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'company', 'generated_at']
    list_filter = ['report_type']
