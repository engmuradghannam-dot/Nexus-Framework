from django.contrib import admin

from .models import Customer, SalesOrder, SalesOrderItem

admin.site.register(Customer)
admin.site.register(SalesOrder)
admin.site.register(SalesOrderItem)
