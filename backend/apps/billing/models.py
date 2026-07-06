"""
Billing and subscription management for SaaS ERP.
Integrates with Stripe for payments.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


class Plan(models.Model):
    """Subscription plans available to tenants."""
    BILLING_INTERVALS = [
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_price_id = models.CharField(max_length=255, unique=True, blank=True)
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    tier = models.CharField(max_length=20, choices=[
        ('free', 'Free'), ('starter', 'Starter'),
        ('professional', 'Professional'), ('enterprise', 'Enterprise')
    ])

    billing_interval = models.CharField(max_length=10, choices=BILLING_INTERVALS, default='month')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Feature limits
    max_users = models.PositiveIntegerField(default=5)
    max_warehouses = models.PositiveIntegerField(default=2)
    max_branches = models.PositiveIntegerField(default=1)
    storage_limit_gb = models.PositiveIntegerField(default=1)
    includes_api_access = models.BooleanField(default=True)
    includes_advanced_reporting = models.BooleanField(default=False)
    includes_ai_features = models.BooleanField(default=False)
    includes_white_label = models.BooleanField(default=False)
    enabled_modules = models.JSONField(default=list, blank=True, help_text="Module codes included in this plan")

    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Show on pricing page")
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'price_monthly']
        db_table = 'public"."billing_plan'

    def __str__(self):
        return f"{self.name} ({self.billing_interval})"

    def get_price(self, interval=None):
        if interval == 'year':
            return self.price_yearly
        return self.price_monthly


class Subscription(models.Model):
    """Tenant subscription tracking."""
    STATUS_CHOICES = [
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('paused', 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')

    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')

    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'public"."billing_subscription'

    def is_active(self):
        return self.status in ('trialing', 'active') and self.current_period_end > timezone.now()

    def days_until_renewal(self):
        if self.current_period_end:
            return (self.current_period_end - timezone.now()).days
        return 0

    def can_cancel(self):
        return self.status in ('trialing', 'active', 'past_due')


class Invoice(models.Model):
    """Invoice for tenant subscription charges."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('uncollectible', 'Uncollectible'),
        ('void', 'Void'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)

    stripe_invoice_id = models.CharField(max_length=255, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    currency = models.CharField(max_length=3, default='USD')

    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    pdf_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'public"."billing_invoice'

    def __str__(self):
        return self.invoice_number

    def calculate_totals(self):
        self.tax_amount = self.subtotal * (self.tax_percent / 100)
        self.total = self.subtotal + self.tax_amount
        self.amount_due = self.total - self.amount_paid
        self.save(update_fields=['tax_amount', 'total', 'amount_due'])

    def mark_paid(self):
        self.status = 'paid'
        self.amount_paid = self.total
        self.amount_due = 0
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'amount_paid', 'amount_due', 'paid_at'])


class Payment(models.Model):
    """Individual payment records."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)

    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    payment_method = models.CharField(max_length=50, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)

    failure_message = models.TextField(blank=True)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'public"."billing_payment'


class UsageRecord(models.Model):
    """Track metered usage for billing (API calls, storage, etc.)."""
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='usage_records')
    metric_name = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    stripe_usage_record_id = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'metric_name', 'timestamp']),
        ]
        db_table = 'public"."billing_usagerecord'
