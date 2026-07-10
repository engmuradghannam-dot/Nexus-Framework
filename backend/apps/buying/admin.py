from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem, Supplier

admin.site.register(Supplier)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
