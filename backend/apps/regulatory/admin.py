from django.contrib import admin
from .models import Regulation, ComplianceCheck, Risk


@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'jurisdiction', 'severity', 'status',
                    'effective_date', 'review_date', 'is_overdue', 'is_active']
    list_filter = ['severity', 'status', 'jurisdiction', 'is_active']
    search_fields = ['title', 'code', 'description']
    date_hierarchy = 'effective_date'


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['regulation', 'branch', 'result', 'score', 'auditor', 'checked_at']
    list_filter = ['result']


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ['title', 'risk_level', 'likelihood', 'impact', 'status', 'owner']
    list_filter = ['status', 'likelihood', 'impact']
