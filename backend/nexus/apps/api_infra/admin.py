from django.contrib import admin
from .models import Webhook, WebhookDelivery, FileUpload, APIRequestLog, BatchOperation
from .tenancy import Tenant, Domain, TenantUser

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'success_count', 'fail_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']

@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event', 'status', 'response_status', 'created_at']
    list_filter = ['status', 'event']

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'file_type', 'file_size', 'storage', 'uploaded_by', 'created_at']
    list_filter = ['storage', 'file_type']

@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'response_status', 'duration_ms', 'created_at']
    list_filter = ['method', 'response_status']

@admin.register(BatchOperation)
class BatchOperationAdmin(admin.ModelAdmin):
    list_display = ['name', 'operation', 'model_name', 'status', 'success_count', 'fail_count', 'created_at']
    list_filter = ['operation', 'status']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'plan', 'is_active', 'created_on']
    list_filter = ['plan', 'is_active']

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']

@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'user', 'role', 'is_active']
    list_filter = ['role', 'is_active']
