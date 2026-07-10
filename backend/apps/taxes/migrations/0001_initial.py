# Generated manually for Nexus Framework

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CountryTaxProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("country_code", models.CharField(db_index=True, max_length=2, unique=True)),
                ("country_name", models.CharField(max_length=100)),
                ("currency_code", models.CharField(default="USD", max_length=3)),
                ("vat_enabled", models.BooleanField(default=True)),
                ("vat_standard_rate", models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("vat_reduced_rate", models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("vat_zero_rate_enabled", models.BooleanField(default=False)),
                ("sales_tax_enabled", models.BooleanField(default=False)),
                ("sales_tax_rate", models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("withholding_tax_enabled", models.BooleanField(default=False)),
                ("withholding_tax_rate", models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("tax_id_format", models.CharField(blank=True, help_text="Regex pattern for tax ID validation", max_length=50)),
                ("tax_id_example", models.CharField(blank=True, max_length=50)),
                ("fiscal_year_start", models.DateField(blank=True, null=True)),
                ("fiscal_year_end", models.DateField(blank=True, null=True)),
                ("e_invoicing_mandatory", models.BooleanField(default=False)),
                ("e_invoicing_threshold", models.DecimalField(decimal_places=2, default=0.0, max_digits=15)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["country_name"],
                "verbose_name": "Country Tax Profile",
                "verbose_name_plural": "Country Tax Profiles",
            },
        ),
        migrations.CreateModel(
            name="TaxRate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("tax_type", models.CharField(choices=[("vat_standard", "VAT Standard"), ("vat_reduced", "VAT Reduced"), ("vat_zero", "VAT Zero"), ("sales", "Sales Tax"), ("withholding", "Withholding Tax"), ("excise", "Excise Tax"), ("customs", "Customs Duty"), ("stamp", "Stamp Duty"), ("environmental", "Environmental Tax"), ("digital", "Digital Services Tax")], default="vat_standard", max_length=20)),
                ("rate", models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("description", models.TextField(blank=True)),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("country", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tax_rates", to="taxes.countrytaxprofile")),
            ],
            options={
                "ordering": ["-effective_date", "tax_type"],
                "verbose_name": "Tax Rate",
                "verbose_name_plural": "Tax Rates",
            },
        ),
        migrations.AddConstraint(
            model_name="taxrate",
            constraint=models.UniqueConstraint(fields=("country", "tax_type", "effective_date"), name="unique_tax_rate_country_type_date"),
        ),
        migrations.CreateModel(
            name="TaxRule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("rule_type", models.CharField(choices=[("exemption", "Exemption"), ("reduction", "Rate Reduction"), ("reverse_charge", "Reverse Charge"), ("oss", "One-Stop-Shop"), ("threshold", "Distance Selling Threshold"), ("digital", "Digital Services Rule"), ("b2b", "B2B Special Rule"), ("b2c", "B2C Special Rule")], max_length=20)),
                ("description", models.TextField()),
                ("conditions", models.JSONField(default=dict, help_text="JSON logic for rule conditions")),
                ("tax_rate_override", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("is_active", models.BooleanField(default=True)),
                ("priority", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("country", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tax_rules", to="taxes.countrytaxprofile")),
            ],
            options={
                "ordering": ["priority", "-created_at"],
                "verbose_name": "Tax Rule",
                "verbose_name_plural": "Tax Rules",
            },
        ),
        migrations.CreateModel(
            name="TaxCalculation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reference_number", models.CharField(db_index=True, max_length=100)),
                ("base_amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("tax_amount", models.DecimalField(decimal_places=2, default=0.0, max_digits=15)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0.0, max_digits=15)),
                ("applied_tax_rates", models.JSONField(default=list)),
                ("customer_vat_id", models.CharField(blank=True, max_length=50)),
                ("is_b2b", models.BooleanField(default=False)),
                ("transaction_date", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("calculated", "Calculated"), ("applied", "Applied"), ("cancelled", "Cancelled")], default="draft", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("country", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="calculations", to="taxes.countrytaxprofile")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Tax Calculation",
                "verbose_name_plural": "Tax Calculations",
            },
        ),
    ]
