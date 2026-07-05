from django.db import models
from apps.core.models import Company, Warehouse

class ItemGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_groups')
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=100, unique=True)
    item_name = models.CharField(max_length=255)
    item_group = models.ForeignKey(ItemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    standard_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_stock_item = models.BooleanField(default=True)
    is_purchase_item = models.BooleanField(default=True)
    is_sales_item = models.BooleanField(default=True)
    reorder_level = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reorder_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default='Unit')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name

class StockEntry(models.Model):
    ENTRY_TYPES = [('Receipt', 'Receipt'), ('Issue', 'Issue'), ('Transfer', 'Transfer')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    posting_date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.entry_type} - {self.item.item_code}"
