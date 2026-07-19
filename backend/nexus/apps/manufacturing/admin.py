from django.contrib import admin
from .models import (
    WorkCenter, BOM, BOMItem, Routing, RoutingOperation,
    ManufacturingOrder, ManufacturingOrderOperation,
    MaterialRequisition, MaterialRequisitionItem
)

@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'company', 'status', 'capacity_per_hour', 'is_active']
    list_filter = ['status', 'is_active', 'company']
    search_fields = ['name', 'code']

@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ['product', 'version', 'is_active', 'is_default', 'item_count', 'total_cost']
    list_filter = ['is_active', 'is_default']
    search_fields = ['product__name']

@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ['bom', 'component', 'quantity', 'unit_cost', 'scrap_percentage']
    search_fields = ['bom__product__name', 'component__name']

@admin.register(Routing)
class RoutingAdmin(admin.ModelAdmin):
    list_display = ['product', 'version', 'is_active', 'is_default', 'operation_count']
    list_filter = ['is_active', 'is_default']
    search_fields = ['product__name']

@admin.register(RoutingOperation)
class RoutingOperationAdmin(admin.ModelAdmin):
    list_display = ['routing', 'sequence', 'name', 'work_center', 'setup_time', 'run_time_per_unit']
    list_filter = ['work_center']

@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'product', 'company', 'status', 'priority', 'quantity', 'quantity_produced', 'completion_percentage']
    list_filter = ['status', 'priority', 'company']
    search_fields = ['order_number', 'product__name']

@admin.register(ManufacturingOrderOperation)
class ManufacturingOrderOperationAdmin(admin.ModelAdmin):
    list_display = ['manufacturing_order', 'sequence', 'status', 'work_center', 'quantity_produced']
    list_filter = ['status']

@admin.register(MaterialRequisition)
class MaterialRequisitionAdmin(admin.ModelAdmin):
    list_display = ['requisition_number', 'manufacturing_order', 'warehouse', 'status', 'total_items']
    list_filter = ['status']

@admin.register(MaterialRequisitionItem)
class MaterialRequisitionItemAdmin(admin.ModelAdmin):
    list_display = ['requisition', 'product', 'quantity_requested', 'quantity_issued', 'fulfillment_percentage']
