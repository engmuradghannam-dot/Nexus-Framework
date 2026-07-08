from django.contrib import admin
from .models import User, CompanyProfile, Branch, Warehouse


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'username', 'department', 'job_title',
        'permissions_level', 'is_department_head', 'is_active'
    ]
    list_filter = ['permissions_level', 'is_department_head', 'is_active', 'department']
    search_fields = ['email', 'username', 'department']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('HR & Permissions', {
            'fields': ('department', 'job_title', 'permissions_level',
                       'is_department_head', 'avatar')
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'industry_vertical', 'super_admin',
        'multi_branch_enabled', 'multi_warehouse_enabled',
        'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'industry_vertical',
        'multi_branch_enabled', 'multi_warehouse_enabled'
    ]
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'code', 'industry_vertical', 'super_admin')
        }),
        ('Modules & Features', {
            'fields': ('modules_enabled', 'features_enabled')
        }),
        ('Settings', {
            'fields': (
                'currency', 'timezone',
                'multi_branch_enabled', 'multi_warehouse_enabled'
            )
        }),
        ('Contact', {
            'fields': ('logo', 'address', 'phone', 'email', 'website')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'code', 'address']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'branch', 'parent_warehouse',
        'capacity', 'current_occupancy', 'occupancy_rate', 'is_active'
    ]
    list_filter = ['is_active', 'branch']
    search_fields = ['name', 'code']
