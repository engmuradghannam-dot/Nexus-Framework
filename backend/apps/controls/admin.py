from django.contrib import admin

from apps.core.admin_site import admin_site

from .models import AIAgent, FormControl, Industry, IndustryControl, MasterEntity


@admin.register(Industry, site=admin_site)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "category"]
    list_filter = ["category"]
    search_fields = ["code", "name", "description"]


@admin.register(IndustryControl, site=admin_site)
class IndustryControlAdmin(admin.ModelAdmin):
    list_display = ["control_id", "control_name", "industry", "module", "required"]
    list_filter = ["industry", "module", "required", "compliance"]
    search_fields = ["control_id", "control_name", "description"]


@admin.register(AIAgent, site=admin_site)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ["name", "industry", "database_entity"]
    list_filter = ["industry"]
    search_fields = ["name", "responsibility"]


@admin.register(MasterEntity, site=admin_site)
class MasterEntityAdmin(admin.ModelAdmin):
    list_display = ["name", "entity_type", "usage"]
    search_fields = ["name"]


@admin.register(FormControl, site=admin_site)
class FormControlAdmin(admin.ModelAdmin):
    list_display = ["form_name", "input_name", "input_type", "status", "priority"]
    list_filter = ["status", "priority", "input_type", "form_name"]
    search_fields = ["form_name", "input_name"]
