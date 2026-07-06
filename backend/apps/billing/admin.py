from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'tier', 'price_monthly', 'price_yearly', 'currency', 'is_active', 'is_public']
    list_filter = ['tier', 'is_active', 'is_public']
    search_fields = ['name', 'code']
    fieldsets = (
        ('Basic', {'fields': ('name', 'code', 'description', 'tier', 'stripe_price_id')}),
        ('Pricing', {'fields': ('billing_interval', 'price_monthly', 'price_yearly', 'currency')}),
        ('Limits', {'fields': ('max_users', 'max_warehouses', 'max_branches', 'storage_limit_gb')}),
        ('Features', {'fields': ('includes_api_access', 'includes_advanced_reporting', 'includes_ai_features', 'includes_white_label', 'enabled_modules')}),
        ('Status', {'fields': ('is_active', 'is_public', 'sort_order')}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['status', 'plan', 'cancel_at_period_end']
    search_fields = ['tenant__name', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'tenant', 'status', 'total', 'amount_due', 'due_date', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['invoice_number', 'tenant__name', 'stripe_invoice_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'currency', 'payment_method', 'created_at']
    search_fields = ['stripe_payment_intent_id', 'tenant__name']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'metric_name', 'quantity', 'unit', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
    search_fields = ['tenant__name']
