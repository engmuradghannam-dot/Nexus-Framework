from django.contrib import admin
from .models import (
    ProductCatalog, Customer, Cart, CartItem, Order, OrderItem,
    POSession, POSTransaction, POSTransactionItem
)

@admin.register(ProductCatalog)
class ProductCatalogAdmin(admin.ModelAdmin):
    list_display = ['product', 'sale_price', 'is_featured', 'is_online']
    list_filter = ['is_featured', 'is_online']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'type', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'email']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'payment_status', 'total']
    list_filter = ['status', 'payment_status']
    search_fields = ['order_number']

@admin.register(POSession)
class POSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'branch', 'cashier', 'status', 'opened_at']
    list_filter = ['status', 'branch']

@admin.register(POSTransaction)
class POSTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'type', 'payment_method', 'total']
    list_filter = ['type', 'payment_method']
