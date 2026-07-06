from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'tier', 'price_monthly', 'price_yearly', 'currency', 'is_active', 'is_public']
    list_filter = ['tier', 'is_active', 'is_public']
    search_fields = ['name', 'code']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['status', 'plan', 'cancel_at_period_end']
    search_fields = ['tenant__name', 'stripe_subscription_id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'tenant', 'status', 'total', 'amount_due', 'due_date', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['invoice_number', 'tenant__name', 'stripe_invoice_id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'currency', 'payment_method', 'created_at']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'metric_name', 'quantity', 'unit', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
