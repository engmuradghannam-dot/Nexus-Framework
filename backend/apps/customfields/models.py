"""User-defined custom fields per module (tenant-scoped, no code required)."""
from django.db import models


class CustomField(models.Model):
    TYPES = [
        ("text", "Text"), ("number", "Number"), ("date", "Date"),
        ("select", "Select"), ("boolean", "Boolean"), ("textarea", "Text Area"),
    ]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    module = models.CharField(max_length=60, db_index=True)
    field_key = models.CharField(max_length=60)
    label = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120, blank=True)
    field_type = models.CharField(max_length=12, choices=TYPES, default="text")
    options = models.JSONField(default=list, blank=True)   # for select
    required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "custom_fields"
        ordering = ["module", "order", "id"]
        unique_together = ["tenant", "module", "field_key"]

    def __str__(self):
        return f"{self.module}.{self.field_key}"
