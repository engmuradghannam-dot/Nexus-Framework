from django.contrib import admin
from .models import BOM, BOMItem, WorkOrder

admin.site.register(BOM)
admin.site.register(BOMItem)
admin.site.register(WorkOrder)
