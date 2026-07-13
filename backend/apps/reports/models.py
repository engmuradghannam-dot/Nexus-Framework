"""User-defined reports over module records / invoices (tenant-scoped)."""
from django.db import models


class ReportDefinition(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    name = models.CharField(max_length=150)
    source = models.CharField(max_length=60)              # module name or 'invoices'
    columns = models.JSONField(default=list, blank=True)  # ["field1", ...]
    filters = models.JSONField(default=list, blank=True)  # [{"field","op","value"}]
    group_by = models.CharField(max_length=60, blank=True)
    aggregate = models.CharField(max_length=60, blank=True)  # "count" or "sum:<field>"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "report_definitions"
        ordering = ["name"]

    def __str__(self):
        return self.name
