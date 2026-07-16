from django.contrib import admin
from .models import Company, Branch, Warehouse, SubWarehouse, Department, HRProfile

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'is_active', 'created_at']
    list_filter = ['company', 'is_active']
    search_fields = ['name']

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'branch', 'is_main']
    list_filter = ['is_main']
    search_fields = ['name', 'code']

@admin.register(SubWarehouse)
class SubWarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'warehouse']
    search_fields = ['name', 'code']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'department', 'branch', 'role', 'is_active']
    list_filter = ['is_active', 'department']
    search_fields = ['user__username', 'employee_id']
