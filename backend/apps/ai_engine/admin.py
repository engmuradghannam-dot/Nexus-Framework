"""AI Engine Admin"""
from django.contrib import admin
from .models import (
    AIAgent, AIConversation, AIPrediction, FeatureFlag,
    LicensePackage, DeploymentTemplate, WorkflowTemplate,
    APIIntegration, DataDictionary
)

@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent_type', 'industry', 'model_name', 'status', 'is_enabled', 'usage_count']
    list_filter = ['industry', 'status', 'is_enabled']
    search_fields = ['name', 'agent_type']

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ['agent', 'user', 'tokens_used', 'response_time_ms', 'created_at']
    list_filter = ['agent']

@admin.register(AIPrediction)
class AIPredictionAdmin(admin.ModelAdmin):
    list_display = ['agent', 'prediction_type', 'confidence_score', 'is_actioned', 'created_at']
    list_filter = ['prediction_type', 'is_actioned']

@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['feature_name', 'feature_code', 'module', 'is_enabled', 'is_premium', 'license_tier']
    list_filter = ['module', 'is_enabled', 'is_premium', 'license_tier']
    search_fields = ['feature_name', 'feature_code']

@admin.register(LicensePackage)
class LicensePackageAdmin(admin.ModelAdmin):
    list_display = ['company', 'tier', 'billing_cycle', 'max_users', 'is_active', 'start_date', 'end_date']
    list_filter = ['tier', 'billing_cycle', 'is_active']

@admin.register(DeploymentTemplate)
class DeploymentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'country', 'company_size', 'recommended_license', 'is_active']
    list_filter = ['industry', 'company_size', 'is_active']

@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_system', 'is_active']
    list_filter = ['category', 'is_system', 'is_active']

@admin.register(APIIntegration)
class APIIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'provider', 'status', 'is_active', 'last_sync']
    list_filter = ['integration_type', 'status', 'is_active']

@admin.register(DataDictionary)
class DataDictionaryAdmin(admin.ModelAdmin):
    list_display = ['entity_name', 'field_name', 'field_type', 'is_required', 'is_unique', 'module']
    list_filter = ['module', 'is_required', 'is_active']
    search_fields = ['entity_name', 'field_name']
