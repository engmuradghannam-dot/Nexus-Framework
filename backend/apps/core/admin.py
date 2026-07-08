from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Branch, Warehouse


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'department', 'job_title',
                    'permissions_level', 'is_department_head', 'is_active']
    list_filter = ['permissions_level', 'is_department_head', 'is_active', 'department']
    search_fields = ['email', 'username', 'department']
    fieldsets = UserAdmin.fieldsets + (
        ('HR & Permissions', {
            'fields': ('department', 'job_title', 'permissions_level',
                       'is_department_head', 'avatar')
        }),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'address']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'branch', 'parent_warehouse',
                    'capacity', 'current_occupancy', 'occupancy_rate', 'is_active']
    list_filter = ['is_active', 'branch']
    search_fields = ['name', 'code']
