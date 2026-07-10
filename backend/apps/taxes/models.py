import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class CountryTaxProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country_code = models.CharField(max_length=2, unique=True, db_index=True)
    country_name = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=3, default="USD")
    vat_enabled = models.BooleanField(default=True)
    vat_standard_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vat_reduced_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True
    )
    vat_zero_rate_enabled = models.BooleanField(default=False)
    sales_tax_enabled = models.BooleanField(default=False)
    sales_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    withholding_tax_enabled = models.BooleanField(default=False)
    withholding_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    tax_id_format = models.CharField(max_length=50, blank=True, help_text="Regex pattern for tax ID validation")
    tax_id_example = models.CharField(max_length=50, blank=True)
    fiscal_year_start = models.DateField(blank=True, null=True)
    fiscal_year_end = models.DateField(blank=True, null=True)
    e_invoicing_mandatory = models.BooleanField(default=False)
    e_invoicing_threshold = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["country_name"]
        verbose_name = "Country Tax Profile"
        verbose_name_plural = "Country Tax Profiles"

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class TaxRate(models.Model):
    TAX_TYPE_CHOICES = [
        ("vat_standard", "VAT Standard"),
        ("vat_reduced", "VAT Reduced"),
        ("vat_zero", "VAT Zero"),
        ("sales", "Sales Tax"),
        ("withholding", "Withholding Tax"),
        ("excise", "Excise Tax"),
        ("customs", "Customs Duty"),
        ("stamp", "Stamp Duty"),
        ("environmental", "Environmental Tax"),
        ("digital", "Digital Services Tax"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(
        CountryTaxProfile, on_delete=models.CASCADE, related_name="tax_rates"
    )
    name = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default="vat_standard")
    rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.TextField(blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date", "tax_type"]
        verbose_name = "Tax Rate"
        verbose_name_plural = "Tax Rates"
        unique_together = [["country", "tax_type", "effective_date"]]

    def __str__(self):
        return f"{self.name} - {self.rate}% ({self.country.country_code})"


class TaxRule(models.Model):
    RULE_TYPE_CHOICES = [
        ("exemption", "Exemption"),
        ("reduction", "Rate Reduction"),
        ("reverse_charge", "Reverse Charge"),
        ("oss", "One-Stop-Shop"),
        ("threshold", "Distance Selling Threshold"),
        ("digital", "Digital Services Rule"),
        ("b2b", "B2B Special Rule"),
        ("b2c", "B2C Special Rule"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(
        CountryTaxProfile, on_delete=models.CASCADE, related_name="tax_rules"
    )
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    description = models.TextField()
    conditions = models.JSONField(default=dict, help_text="JSON logic for rule conditions")
    tax_rate_override = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "-created_at"]
        verbose_name = "Tax Rule"
        verbose_name_plural = "Tax Rules"

    def __str__(self):
        return f"{self.name} ({self.country.country_code})"


class TaxCalculation(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("calculated", "Calculated"),
        ("applied", "Applied"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(
        CountryTaxProfile, on_delete=models.PROTECT, related_name="calculations"
    )
    reference_number = models.CharField(max_length=100, db_index=True)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    applied_tax_rates = models.JSONField(default=list)
    customer_vat_id = models.CharField(max_length=50, blank=True)
    is_b2b = models.BooleanField(default=False)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tax Calculation"
        verbose_name_plural = "Tax Calculations"

    def __str__(self):
        return f"Calc {self.reference_number} - {self.country.country_code}"

    def calculate(self):
        self.tax_amount = Decimal("0.00")
        self.total_amount = self.base_amount
        self.applied_tax_rates = []

        # Get active tax rates for the country
        rates = self.country.tax_rates.filter(is_active=True)

        for rate in rates:
            if self.is_b2b and rate.tax_type == "vat_standard":
                # B2B reverse charge logic
                continue

            tax = (self.base_amount * rate.rate) / Decimal("100")
            self.tax_amount += tax
            self.applied_tax_rates.append({
                "tax_type": rate.tax_type,
                "rate": str(rate.rate),
                "amount": str(tax.quantize(Decimal("0.01"))),
                "name": rate.name,
            })

        self.total_amount = self.base_amount + self.tax_amount
        self.status = "calculated"
        return self
