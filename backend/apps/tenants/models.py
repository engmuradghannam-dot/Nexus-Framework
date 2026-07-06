"""
Multi-tenancy core models for SaaS ERP.
Implements schema-per-tenant isolation with PostgreSQL.
"""
from django.db import models, connection
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class TenantManager(models.Manager):
    def get_by_natural_key(self, schema_name):
        return self.get(schema_name=schema_name)


class Tenant(models.Model):
    """
    Represents a SaaS tenant (company/organization).
    Each tenant gets its own PostgreSQL schema for true data isolation.
    """
    TIER_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial'),
        ('trial_expired', 'Trial Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schema_name = models.CharField(
        max_length=63, unique=True,
        validators=[RegexValidator(
            regex=r'^[a-z][a-z0-9_]*$',
            message='Schema name must start with a letter and contain only lowercase letters, numbers, and underscores'
        )],
        help_text="PostgreSQL schema name for this tenant"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=63, unique=True, help_text="Subdomain: {slug}.nexus-erp.com")

    # Billing/Tier
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='trial')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # Limits per tier
    max_users = models.PositiveIntegerField(default=5)
    max_warehouses = models.PositiveIntegerField(default=2)
    max_branches = models.PositiveIntegerField(default=1)
    storage_limit_mb = models.PositiveIntegerField(default=1024)

    # Stripe
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    # Features/modules enabled
    enabled_modules = models.JSONField(default=list, blank=True, help_text="List of module codes enabled")

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    timezone = models.CharField(max_length=50, default='Asia/Riyadh')

    # Branding
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default='#2563eb', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-created_at']
        db_table = 'public"."tenants_tenant'

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def is_active(self):
        if self.status == 'cancelled':
            return False
        if self.status == 'trial' and self.trial_ends_at and self.trial_ends_at < timezone.now():
            return False
        return self.status in ('active', 'trial')

    def create_schema(self):
        """Create PostgreSQL schema for this tenant."""
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')

    def drop_schema(self):
        """Drop tenant schema (dangerous!)."""
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{self.schema_name}" CASCADE')

    def get_enabled_modules(self):
        """Return set of enabled module codes."""
        return set(self.enabled_modules or [])

    def has_module(self, module_code):
        """Check if a module is enabled for this tenant."""
        return module_code in self.get_enabled_modules()


class Domain(models.Model):
    """
    Custom domains pointing to a tenant.
    Primary: slug.nexus-erp.com
    Custom: client-domain.com
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)
    ssl_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'public"."tenants_domain'

    def __str__(self):
        return self.domain


class TenantUsage(models.Model):
    """Track resource usage per tenant for billing and limits."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='usage')

    current_users = models.PositiveIntegerField(default=0)
    current_warehouses = models.PositiveIntegerField(default=0)
    current_branches = models.PositiveIntegerField(default=0)
    storage_used_mb = models.PositiveIntegerField(default=0)

    api_calls_this_month = models.PositiveIntegerField(default=0)
    documents_generated_this_month = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'public"."tenants_tenantusage'

    def check_limits(self, resource):
        """Check if tenant has exceeded limits."""
        limits = {
            'users': (self.current_users, self.tenant.max_users),
            'warehouses': (self.current_warehouses, self.tenant.max_warehouses),
            'branches': (self.current_branches, self.tenant.max_branches),
            'storage': (self.storage_used_mb, self.tenant.storage_limit_mb),
        }
        current, max_val = limits.get(resource, (0, 0))
        return current < max_val

    def increment(self, resource, amount=1):
        """Increment usage counter."""
        field_map = {
            'users': 'current_users',
            'warehouses': 'current_warehouses',
            'branches': 'current_branches',
            'storage': 'storage_used_mb',
            'api_calls': 'api_calls_this_month',
            'documents': 'documents_generated_this_month',
        }
        field = field_map.get(resource)
        if field:
            from django.db.models import F
            TenantUsage.objects.filter(pk=self.pk).update(**{field: F(field) + amount})
            self.refresh_from_db()
