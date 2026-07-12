"""Generic per-module record store (real CRUD for every ERP module)."""
from django.conf import settings
from django.db import models


class ModuleRecord(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    module = models.CharField(max_length=50, db_index=True)
    data = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="module_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "module_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.module} #{self.pk}"
