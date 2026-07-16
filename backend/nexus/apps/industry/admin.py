from django.contrib import admin
from .models import IndustrySector, Product, Inventory, Supplier, PurchaseOrder, PurchaseOrderItem

@admin.register(IndustrySector)
class IndustrySectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'sector', 'unit_price', 'is_active']
    list_filter = ['is_active', 'sector']
    search_fields = ['name', 'sku']

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'min_reorder_level', 'needs_reorder']
    list_filter = ['warehouse']
    search_fields = ['product__name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'is_active']
    search_fields = ['name']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'warehouse', 'status', 'total_amount', 'created_at']
    list_filter = ['status']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price']
