"""
Industry Vertical Control System
The Industry Vertical is the PARENT of the Company.
It determines what modules, features, and reports appear in the dashboard
based on the Super Admin's configuration.
"""

import uuid

from django.conf import settings
from django.db import models


# ── Industry Vertical (The Control) ──────────────────
class IndustryVertical(models.Model):
    """
    Industry Vertical defines the entire ecosystem for a company.
    Super Admin selects this first, then all modules/features are derived from it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    # Available modules for this vertical (controlled by Super Admin)
    modules_enabled = models.JSONField(
        default=list,
        help_text="List of module codes enabled: ['core', 'pmo', 'industry', 'ai_module', 'regulatory']",
    )

    # Available features per module
    features_config = models.JSONField(
        default=dict,
        help_text="Feature flags per module: {'pmo': ['projects', 'tasks'], 'ai_module': ['predictions']}",
    )

    # Available report templates
    report_templates = models.JSONField(
        default=list, help_text="Available report templates for this vertical"
    )

    # Currency & localization
    default_currency = models.CharField(max_length=3, default="USD")
    supported_currencies = models.JSONField(default=list)

    # Multi-branch/warehouse support
    multi_branch_enabled = models.BooleanField(default=False)
    multi_warehouse_enabled = models.BooleanField(default=False)

    # Industry-specific settings
    compliance_frameworks = models.JSONField(
        default=list, help_text="e.g. ['ISO9001', 'GDPR', 'HIPAA']"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_verticals",
    )

    class Meta:
        db_table = "industry_verticals"
        ordering = ["name"]
        verbose_name = "Industry Vertical"
        verbose_name_plural = "Industry Verticals"

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def module_count(self):
        return len(self.modules_enabled)

    @property
    def feature_count(self):
        return sum(len(v) for v in self.features_config.values())


# ── Vertical Template (Pre-configured Templates) ─────
class VerticalTemplate(models.Model):
    """
    Pre-configured templates for quick vertical setup.
    Super Admin can clone these to create new verticals.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    vertical_type = models.CharField(
        max_length=50,
        choices=[
            ("general_business", "General Business"),
            ("aviation_aerospace", "Aviation & Aerospace"),
            ("healthcare_medical", "Healthcare & Medical"),
            ("banking_finance", "Banking & Finance"),
            ("hospitality_tourism", "Hospitality & Tourism"),
            ("government_public", "Government & Public Sector"),
            ("energy_utilities", "Energy & Utilities"),
            ("education_training", "Education & Training"),
            ("manufacturing", "Manufacturing"),
            ("retail_ecommerce", "Retail & E-commerce"),
            ("real_estate", "Real Estate"),
            ("logistics_transportation", "Logistics & Transportation"),
        ],
    )
    description = models.TextField(blank=True)

    # Default configuration
    default_modules = models.JSONField(default=list)
    default_features = models.JSONField(default=dict)
    default_reports = models.JSONField(default=list)
    default_compliance = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "industry_vertical_templates"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.vertical_type})"


# ── Company (Child of Industry Vertical) ───────────────
class Company(models.Model):
    """
    Company belongs to ONE Industry Vertical.
    All modules, features, and reports are derived from the vertical.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=20, blank=True, unique=True)

    # The PARENT Industry Vertical
    industry_vertical = models.ForeignKey(
        IndustryVertical,
        on_delete=models.PROTECT,
        related_name="companies",
        help_text="The Industry Vertical that controls this company",
    )

    # Optional sector classification within the vertical
    sector = models.ForeignKey(
        "Sector",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
    )

    # Company-specific overrides (optional)
    custom_modules = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional modules beyond the vertical's default",
    )
    custom_features = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional features beyond the vertical's default",
    )

    # Business info
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    revenue = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    employees = models.PositiveIntegerField(default=0)
    headquarters = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)

    # Settings derived from vertical (can override)
    currency = models.CharField(max_length=3, default="USD")
    multi_branch_enabled = models.BooleanField(default=False)
    multi_warehouse_enabled = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "industry_companies"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.industry_vertical.name}]"

    @property
    def effective_modules(self):
        """Return all enabled modules (vertical + custom)"""
        base = set(self.industry_vertical.modules_enabled)
        custom = set(self.custom_modules)
        return sorted(list(base | custom))

    @property
    def effective_features(self):
        """Return all enabled features (vertical + custom)"""
        base = self.industry_vertical.features_config.copy()
        custom = self.custom_features
        for module, features in custom.items():
            if module in base:
                base[module] = list(set(base[module] + features))
            else:
                base[module] = features
        return base

    @property
    def available_reports(self):
        """Return available reports for this company"""
        return self.industry_vertical.report_templates


# ── Sector (Sub-category within Vertical) ──────────────
class Sector(models.Model):
    """Sector within an Industry Vertical"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    industry_vertical = models.ForeignKey(
        IndustryVertical, on_delete=models.CASCADE, related_name="sectors"
    )
    description = models.TextField(blank=True)
    parent_sector = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_sectors",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "industry_sectors"
        ordering = ["industry_vertical__name", "name"]
        unique_together = ["industry_vertical", "code"]

    def __str__(self):
        return f"{self.name} ({self.industry_vertical.code})"


# ── Metric ───────────────────────────────────────────
class Metric(models.Model):
    METRIC_TYPES = [
        ("financial", "Financial"),
        ("operational", "Operational"),
        ("sustainability", "Sustainability"),
        ("innovation", "Innovation"),
        ("compliance", "Compliance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="metrics"
    )
    name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=20, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    period = models.CharField(max_length=20, help_text="e.g. Q1-2026, FY2025")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "industry_metrics"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.company.name} - {self.name} ({self.period})"
