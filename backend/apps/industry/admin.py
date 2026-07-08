from apps.core.admin_site import admin_site
from .models import Sector, Company, Metric


@admin.register(Sector, site=admin_site)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_sector', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'ticker', 'sector', 'market_cap', 'revenue', 'employees', 'is_active']
    list_filter = ['sector', 'is_active']
    search_fields = ['name', 'ticker']


@admin.register(Metric, site=admin_site)
class MetricAdmin(admin.ModelAdmin):
    list_display = ['company', 'name', 'metric_type', 'value', 'unit', 'period']
    list_filter = ['metric_type', 'period']
