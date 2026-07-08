from django.contrib import admin
from apps.core.admin_site import admin_site
from .models import User, Branch, Warehouse


@admin.register(User, site=admin_site)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'department', 'job_title',
                    'permissions_level', 'is_department_head', 'is_active']
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


@admin.register(Branch, site=admin_site)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'address']


@admin.register(Warehouse, site=admin_site)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'branch', 'parent_warehouse',
                    'capacity', 'current_occupancy', 'occupancy_rate', 'is_active']
    list_filter = ['is_active', 'branch']
    search_fields = ['name', 'code']
