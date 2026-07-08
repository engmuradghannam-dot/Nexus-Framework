from django.contrib import admin
from .models import IndustryVertical, VerticalTemplate, Company, Sector, Metric


@admin.register(IndustryVertical)
class IndustryVerticalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'module_count', 'feature_count',
        'multi_branch_enabled', 'multi_warehouse_enabled',
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'multi_branch_enabled', 'multi_warehouse_enabled']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'code', 'description')
        }),
        ('Module Control', {
            'fields': ('modules_enabled', 'features_config')
        }),
        ('Reports & Compliance', {
            'fields': ('report_templates', 'compliance_frameworks')
        }),
        ('Settings', {
            'fields': (
                'default_currency', 'supported_currencies',
                'multi_branch_enabled', 'multi_warehouse_enabled'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(VerticalTemplate)
class VerticalTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'vertical_type', 'is_active', 'created_at']
    list_filter = ['vertical_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'industry_vertical', 'ticker',
        'multi_branch_enabled', 'multi_warehouse_enabled',
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'industry_vertical', 'multi_branch_enabled']
    search_fields = ['name', 'ticker']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry_vertical', 'code', 'is_active']
    list_filter = ['is_active', 'industry_vertical']
    search_fields = ['name', 'code']


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'metric_type', 'value', 'period']
    list_filter = ['metric_type', 'period']
    search_fields = ['name', 'company__name']
