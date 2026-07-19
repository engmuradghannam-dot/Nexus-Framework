"""Tenant (organization) model for multi-tenant data isolation."""
from django.db import models


class Tenant(models.Model):
    PLANS = [("free", "Free"), ("pro", "Pro"), ("enterprise", "Enterprise")]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    subdomain = models.CharField(max_length=80, blank=True, db_index=True)
    plan = models.CharField(max_length=12, choices=PLANS, default="free")
    is_active = models.BooleanField(default=True)

    # Database-per-tenant. When database_url is set, this tenant's data lives in
    # its own physical database, registered under db_alias at runtime. When it's
    # blank, the tenant uses the shared default database (row-level isolation),
    # so per-tenant databases can be adopted gradually, tenant by tenant, without
    # migrating everyone at once.
    database_url = models.CharField(
        max_length=500, blank=True,
        help_text="If set, this tenant's own database (e.g. postgres://…). "
        "Blank means the shared default database.",
    )

    @property
    def db_alias(self):
        """The Django connection alias for this tenant's database, or 'default'
        when it has no dedicated one."""
        return f"tenant_{self.pk}" if self.database_url else "default"

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenants"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TenantScopedModel(models.Model):
    """Abstract base: rows belong to a tenant and are isolated per tenant."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )

    class Meta:
        abstract = True
