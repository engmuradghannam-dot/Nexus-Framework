from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain, TenantUser, TenantUsage


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


class TenantUsageInline(admin.StackedInline):
    model = TenantUsage
    readonly_fields = ['current_users', 'current_warehouses', 'current_branches', 
                       'storage_used_mb', 'api_calls_this_month', 'documents_generated_this_month']


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'slug', 'tier', 'trial_ends_at', 'created_at']
    list_filter = ['tier', 'created_at']
    search_fields = ['name', 'slug', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [DomainInline, TenantUsageInline]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary', 'ssl_enabled']
    list_filter = ['is_primary', 'ssl_enabled']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    filter_horizontal = ['tenants']
