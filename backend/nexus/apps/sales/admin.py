from django.contrib import admin

from .models import Backorder, Delivery, Invoice, Quotation, SalesOrder, SalesOrderItem

admin.site.register(SalesOrder)
admin.site.register(SalesOrderItem)
admin.site.register(Backorder)
admin.site.register(Delivery)
admin.site.register(Quotation)
admin.site.register(Invoice)
