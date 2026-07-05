from django.db import models
from apps.core.models import Company
from apps.hr.models import Employee

class AssetCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='asset_categories')
    name = models.CharField(max_length=255)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('In Maintenance', 'In Maintenance'), ('Disposed', 'Disposed')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='assets')
    asset_name = models.CharField(max_length=255)
    asset_code = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    custodian = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.asset_name
