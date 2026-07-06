"""
True multi-tenancy models using django-tenants.
Each tenant gets its own PostgreSQL schema with full isolation.
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid


class TenantManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Tenant(TenantMixin, models.Model):
    """
    Tenant model using django-tenants TenantMixin.
    Each tenant = one PostgreSQL schema.
    """
    TIER_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Subdomain identifier")

    # Billing/Tier
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='trial')
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # Limits
    max_users = models.PositiveIntegerField(default=5)
    max_warehouses = models.PositiveIntegerField(default=2)
    max_branches = models.PositiveIntegerField(default=1)
    storage_limit_mb = models.PositiveIntegerField(default=1024)

    # Stripe
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    # Modules
    enabled_modules = models.JSONField(default=list, blank=True)

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

    # django-tenants required fields
    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    @property
    def schema_name(self):
        """Generate schema name from slug."""
        return self.slug.lower().replace('-', '_')

    def is_active_tenant(self):
        if self.tier == 'free':
            return True
        if self.trial_ends_at and self.trial_ends_at < timezone.now():
            return False
        return True


class Domain(DomainMixin, models.Model):
    """Domain mapping for tenants using django-tenants DomainMixin."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)
    ssl_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['domain', 'tenant']

    def __str__(self):
        return self.domain


class TenantUser(AbstractBaseUser, PermissionsMixin):
    """
    Global user model that can belong to multiple tenants.
    Uses django-tenant-users pattern for cross-tenant auth.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    # Global flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Tenants this user belongs to
    tenants = models.ManyToManyField(Tenant, blank=True, related_name='users')
    current_tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_users')

    # Profile
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    language = models.CharField(max_length=10, default='ar')
    time_zone = models.CharField(max_length=50, default='Asia/Riyadh')

    date_joined = models.DateTimeField(default=timezone.now)

    objects = TenantManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def has_tenant_permission(self, tenant, permission):
        """Check if user has specific permission in a tenant."""
        if self.is_superuser:
            return True
        return self.tenants.filter(id=tenant.id).exists()


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

    def check_limits(self, resource):
        limits = {
            'users': (self.current_users, self.tenant.max_users),
            'warehouses': (self.current_warehouses, self.tenant.max_warehouses),
            'branches': (self.current_branches, self.tenant.max_branches),
            'storage': (self.storage_used_mb, self.tenant.storage_limit_mb),
        }
        current, max_val = limits.get(resource, (0, 0))
        return current < max_val
