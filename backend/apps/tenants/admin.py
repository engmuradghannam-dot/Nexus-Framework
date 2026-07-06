from django.contrib import admin
from .models import Tenant, Domain, TenantUsage


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


class TenantUsageInline(admin.StackedInline):
    model = TenantUsage
    readonly_fields = ['current_users', 'current_warehouses', 'current_branches', 
                       'storage_used_mb', 'api_calls_this_month', 'documents_generated_this_month']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'slug', 'tier', 'status', 'email', 'created_at']
    list_filter = ['tier', 'status', 'country', 'created_at']
    search_fields = ['name', 'schema_name', 'slug', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [DomainInline, TenantUsageInline]
    fieldsets = (
        ('Basic', {'fields': ('id', 'name', 'slug', 'schema_name', 'email', 'phone')}),
        ('Billing', {'fields': ('tier', 'status', 'trial_ends_at', 'stripe_customer_id', 'stripe_subscription_id')}),
        ('Limits', {'fields': ('max_users', 'max_warehouses', 'max_branches', 'storage_limit_mb')}),
        ('Modules', {'fields': ('enabled_modules',)}),
        ('Branding', {'fields': ('logo_url', 'primary_color')}),
        ('Location', {'fields': ('address', 'country', 'timezone')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'activated_at')}),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary', 'ssl_enabled', 'created_at']
    list_filter = ['is_primary', 'ssl_enabled']
    search_fields = ['domain', 'tenant__name']
