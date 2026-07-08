from django.db import models
from django.conf import settings
import uuid


class Sector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    parent_sector = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='sub_sectors'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'industry_sectors'
        ordering = ['name']

    def __str__(self):
        return self.name


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=20, blank=True, unique=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='companies')
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    revenue = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    employees = models.PositiveIntegerField(default=0)
    headquarters = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'industry_companies'
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name


class Metric(models.Model):
    METRIC_TYPES = [
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('sustainability', 'Sustainability'),
        ('innovation', 'Innovation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=20, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    period = models.CharField(max_length=20, help_text='e.g. Q1-2026, FY2025')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'industry_metrics'
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.company.name} - {self.name} ({self.period})"
