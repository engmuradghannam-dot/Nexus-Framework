from django.contrib import admin
from .models import Role, UserRole, FieldPermission, RecordPermission, PermissionAudit

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_system']
    filter_horizontal = ['django_permissions']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'branch', 'is_active']

@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'field_name', 'access_level']

@admin.register(RecordPermission)
class RecordPermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'access_level']

@admin.register(PermissionAudit)
class PermissionAuditAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'timestamp']
    list_filter = ['action', 'timestamp']
