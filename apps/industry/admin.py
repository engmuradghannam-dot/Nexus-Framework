from django.contrib import admin
from .models import IndustryProject, IndustryMetric


@admin.register(IndustryProject)
class IndustryProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date', 'budget', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'


@admin.register(IndustryMetric)
class IndustryMetricAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'value', 'target', 'unit', 'recorded_at']
    list_filter = ['name', 'recorded_at']
    search_fields = ['name', 'project__name']
