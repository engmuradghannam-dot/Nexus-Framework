from django.contrib import admin
from .models import Sector, Company, Metric


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_sector', 'company_count', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'ticker', 'sector', 'market_cap', 'revenue', 'employees', 'is_active']
    list_filter = ['sector', 'is_active']
    search_fields = ['name', 'ticker']


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ['company', 'name', 'metric_type', 'value', 'unit', 'period']
    list_filter = ['metric_type', 'period']
