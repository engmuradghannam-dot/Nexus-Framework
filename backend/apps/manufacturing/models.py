from django.db import models
from apps.core.models import Company, Warehouse
from apps.inventory.models import Item

class BOM(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boms')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='boms')
    bom_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bom_name

class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=18, decimal_places=2)
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)

class WorkOrder(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_orders')
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True)
    wo_number = models.CharField(max_length=100, unique=True)
    item_to_manufacture = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty_to_produce = models.DecimalField(max_digits=18, decimal_places=2)
    produced_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wo_number
