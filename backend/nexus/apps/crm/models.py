from decimal import Decimal

from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from nexus.apps.core.models import Branch
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import phone_validator


class Customer(models.Model):
    """CRM module - customers table."""

    CUSTOMER_TYPE_CHOICES = [('individual', 'Individual'), ('company', 'Company'), ('government', 'Government')]
    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15'), ('net_30', 'Net 30'), ('net_60', 'Net 60'),
        ('net_90', 'Net 90'), ('cod', 'COD'), ('prepaid', 'Prepaid'),
    ]
    LEAD_SOURCE_CHOICES = [
        ('website', 'Website'), ('referral', 'Referral'), ('campaign', 'Campaign'),
        ('trade_show', 'Trade Show'), ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('lead', 'Lead'), ('prospect', 'Prospect'), ('active', 'Active'),
        ('inactive', 'Inactive'), ('blacklisted', 'Blacklisted'),
    ]

    customer_id = models.CharField(max_length=50, unique=True, blank=True)
    customer_name = models.CharField(max_length=200, validators=[MinLengthValidator(2)])
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='company')
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    tax_number = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='net_30')
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES, blank=True)
    assigned_sales_rep = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_customers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='customers')
    lead_score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    tier = models.CharField(
        max_length=20,
        choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')],
        default='bronze',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = generate_code(Customer, 'customer_id', 'CUST', year=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name

    def outstanding_balance(self):
        # Placeholder aggregation hook for SAL invoices; kept simple/self-contained.
        return getattr(self, '_outstanding_balance', Decimal('0.00'))

    def credit_available(self):
        # CRM-CTRL-001 / SAL-CTRL-001 Credit Limit Check
        return self.credit_limit - self.outstanding_balance()

    def exceeds_credit_limit(self, order_amount):
        return (self.outstanding_balance() + Decimal(order_amount)) > self.credit_limit

    @classmethod
    def find_duplicates(cls, email=None, phone=None, exclude_pk=None):
        # CRM-CTRL-002 Duplicate Prevention
        qs = cls.objects.all()
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        matches = cls.objects.none()
        if email:
            matches = matches | qs.filter(email__iexact=email)
        if phone:
            matches = matches | qs.filter(phone=phone)
        return matches.distinct()

    def calculate_score(self):
        """CRM-RULE-001 Lead Scoring (0-100) based on engagement/interactions."""
        interaction_count = self.interactions.count()
        score = min(interaction_count * 10, 100)
        self.lead_score = score
        self.save(update_fields=['lead_score'])
        return score

    def calculate_clv(self, avg_order_value, purchase_frequency_per_year, customer_lifespan_years):
        # CRM-RULE-004 Customer Lifetime Value
        return (Decimal(avg_order_value) * Decimal(purchase_frequency_per_year) * Decimal(customer_lifespan_years)).quantize(Decimal('0.01'))

    def maybe_upgrade_tier(self, annual_purchases):
        # SAL-RULE-005 Customer Tier Upgrade
        order = ['bronze', 'silver', 'gold', 'platinum']
        thresholds = {'silver': Decimal('50000'), 'gold': Decimal('200000'), 'platinum': Decimal('500000')}
        new_tier = self.tier
        for tier_name in order[1:]:
            if Decimal(annual_purchases) >= thresholds[tier_name]:
                new_tier = tier_name
        if order.index(new_tier) > order.index(self.tier):
            self.tier = new_tier
            self.save(update_fields=['tier'])
        return self.tier


class Contact(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=200, validators=[MinLengthValidator(2)])
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.customer.customer_name})"


class CustomerInteraction(models.Model):
    """Backs CRM-RULE-001 Lead Scoring and CRM-RULE-003 Auto-Follow-up."""

    TYPE_CHOICES = [('call', 'Call'), ('email', 'Email'), ('meeting', 'Meeting'), ('note', 'Note')]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='note')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.interaction_type} @ {self.created_at:%Y-%m-%d}"


class Opportunity(models.Model):
    """CRM module - opportunities table (sales pipeline)."""

    STAGE_CHOICES = [
        ('qualification', 'Qualification'), ('needs_analysis', 'Needs Analysis'),
        ('proposal', 'Proposal'), ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'), ('closed_lost', 'Closed Lost'),
    ]
    STAGE_ORDER = ['qualification', 'needs_analysis', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=200, validators=[MinLengthValidator(2)])
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='qualification')
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    probability = models.PositiveSmallIntegerField(default=10, validators=[MaxValueValidator(100)])
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    expected_close_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    last_activity_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_stage_display()})"

    def validate_stage_transition(self, new_stage):
        # CRM-RULE-002 Opportunity Stage Progression
        if new_stage not in self.STAGE_ORDER:
            return False
        if new_stage in ('closed_won', 'closed_lost'):
            return True
        return self.STAGE_ORDER.index(new_stage) >= self.STAGE_ORDER.index(self.stage)

    @property
    def requires_discount_approval(self):
        # CRM-RULE-005 Discount Approval (> 10%)
        return self.discount_pct > 10

    def needs_follow_up(self, days=7):
        # CRM-RULE-003 Auto-Follow-up
        return (timezone.now() - self.last_activity_at).days >= days
