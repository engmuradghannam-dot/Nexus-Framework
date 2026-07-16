from django.contrib import admin
from .models import Regulation, ComplianceCheck

@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'company', 'status', 'effective_date']
    list_filter = ['status', 'company']

@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['regulation', 'branch', 'result', 'checked_at']
    list_filter = ['result']
