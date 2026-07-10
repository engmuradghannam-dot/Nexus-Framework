"""Seed 5 country tax profiles (SA, AE, US, GB, EG) with rates & rules."""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.taxes.models import CountryTaxProfile, TaxRate, TaxRule


class Command(BaseCommand):
    help = "Seed country tax profiles with rates and rules"

    def handle(self, *args, **options):
        profiles = [
            {
                "country_code": "SA",
                "country_name": "المملكة العربية السعودية",
                "currency_code": "SAR",
                "vat_enabled": True,
                "vat_standard_rate": Decimal("15.00"),
                "vat_reduced_rate": None,
                "vat_zero_rate_enabled": True,
                "sales_tax_enabled": False,
                "sales_tax_rate": Decimal("0.00"),
                "withholding_tax_enabled": True,
                "withholding_tax_rate": Decimal("2.50"),
                "tax_id_format": r"^3\d{13}$",
                "tax_id_example": "300000000000003",
                "e_invoicing_mandatory": True,
                "e_invoicing_threshold": Decimal("50000.00"),
            },
            {
                "country_code": "AE",
                "country_name": "الإمارات العربية المتحدة",
                "currency_code": "AED",
                "vat_enabled": True,
                "vat_standard_rate": Decimal("5.00"),
                "vat_reduced_rate": None,
                "vat_zero_rate_enabled": True,
                "sales_tax_enabled": False,
                "sales_tax_rate": Decimal("0.00"),
                "withholding_tax_enabled": False,
                "withholding_tax_rate": Decimal("0.00"),
                "tax_id_format": r"^\d{15}$",
                "tax_id_example": "123456789012345",
                "e_invoicing_mandatory": False,
                "e_invoicing_threshold": Decimal("100000.00"),
            },
            {
                "country_code": "US",
                "country_name": "United States",
                "currency_code": "USD",
                "vat_enabled": False,
                "vat_standard_rate": Decimal("0.00"),
                "vat_reduced_rate": None,
                "vat_zero_rate_enabled": False,
                "sales_tax_enabled": True,
                "sales_tax_rate": Decimal("7.25"),
                "withholding_tax_enabled": True,
                "withholding_tax_rate": Decimal("24.00"),
                "tax_id_format": r"^\d{2}\-\d{7}$",
                "tax_id_example": "12-3456789",
                "e_invoicing_mandatory": False,
                "e_invoicing_threshold": Decimal("0.00"),
            },
            {
                "country_code": "GB",
                "country_name": "United Kingdom",
                "currency_code": "GBP",
                "vat_enabled": True,
                "vat_standard_rate": Decimal("20.00"),
                "vat_reduced_rate": Decimal("5.00"),
                "vat_zero_rate_enabled": True,
                "sales_tax_enabled": False,
                "sales_tax_rate": Decimal("0.00"),
                "withholding_tax_enabled": False,
                "withholding_tax_rate": Decimal("0.00"),
                "tax_id_format": r"^GB\d{9}$",
                "tax_id_example": "GB123456789",
                "e_invoicing_mandatory": False,
                "e_invoicing_threshold": Decimal("85000.00"),
            },
            {
                "country_code": "EG",
                "country_name": "جمهورية مصر العربية",
                "currency_code": "EGP",
                "vat_enabled": True,
                "vat_standard_rate": Decimal("14.00"),
                "vat_reduced_rate": Decimal("5.00"),
                "vat_zero_rate_enabled": True,
                "sales_tax_enabled": False,
                "sales_tax_rate": Decimal("0.00"),
                "withholding_tax_enabled": True,
                "withholding_tax_rate": Decimal("5.00"),
                "tax_id_format": r"^\d{9}$",
                "tax_id_example": "123456789",
                "e_invoicing_mandatory": True,
                "e_invoicing_threshold": Decimal("50000.00"),
            },
        ]

        created_count = 0
        for data in profiles:
            profile, created = CountryTaxProfile.objects.update_or_create(
                country_code=data["country_code"],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {profile}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated: {profile}"))

        # Seed tax rates for each country
        rates_data = [
            # Saudi Arabia
            {"country_code": "SA", "name": "VAT Standard", "tax_type": "vat_standard", "rate": Decimal("15.00")},
            {"country_code": "SA", "name": "VAT Zero", "tax_type": "vat_zero", "rate": Decimal("0.00")},
            {"country_code": "SA", "name": "Withholding Tax", "tax_type": "withholding", "rate": Decimal("2.50")},
            # UAE
            {"country_code": "AE", "name": "VAT Standard", "tax_type": "vat_standard", "rate": Decimal("5.00")},
            {"country_code": "AE", "name": "VAT Zero", "tax_type": "vat_zero", "rate": Decimal("0.00")},
            # US
            {"country_code": "US", "name": "Sales Tax", "tax_type": "sales", "rate": Decimal("7.25")},
            {"country_code": "US", "name": "Federal Withholding", "tax_type": "withholding", "rate": Decimal("24.00")},
            # UK
            {"country_code": "GB", "name": "VAT Standard", "tax_type": "vat_standard", "rate": Decimal("20.00")},
            {"country_code": "GB", "name": "VAT Reduced", "tax_type": "vat_reduced", "rate": Decimal("5.00")},
            {"country_code": "GB", "name": "VAT Zero", "tax_type": "vat_zero", "rate": Decimal("0.00")},
            # Egypt
            {"country_code": "EG", "name": "VAT Standard", "tax_type": "vat_standard", "rate": Decimal("14.00")},
            {"country_code": "EG", "name": "VAT Reduced", "tax_type": "vat_reduced", "rate": Decimal("5.00")},
            {"country_code": "EG", "name": "Withholding Tax", "tax_type": "withholding", "rate": Decimal("5.00")},
        ]

        rates_created = 0
        for rate_data in rates_data:
            country = CountryTaxProfile.objects.get(country_code=rate_data["country_code"])
            rate, created = TaxRate.objects.update_or_create(
                country=country,
                name=rate_data["name"],
                defaults={
                    "tax_type": rate_data["tax_type"],
                    "rate": rate_data["rate"],
                    "is_active": True,
                },
            )
            if created:
                rates_created += 1

        # Seed tax rules
        rules_data = [
            {"country_code": "SA", "name": "B2B Zero Rate", "rule_type": "exemption", "conditions": {"is_b2b": True, "has_vat_id": True}, "tax_rate_override": Decimal("0.00")},
            {"country_code": "SA", "name": "Export Zero Rate", "rule_type": "exemption", "conditions": {"transaction_type": "export"}, "tax_rate_override": Decimal("0.00")},
            {"country_code": "GB", "name": "B2B Reverse Charge", "rule_type": "reverse_charge", "conditions": {"is_b2b": True, "intra_eu": True}, "tax_rate_override": None},
            {"country_code": "EG", "name": "B2B Zero Rate", "rule_type": "exemption", "conditions": {"is_b2b": True, "has_vat_id": True}, "tax_rate_override": Decimal("0.00")},
        ]

        rules_created = 0
        for rule_data in rules_data:
            country = CountryTaxProfile.objects.get(country_code=rule_data["country_code"])
            rule, created = TaxRule.objects.update_or_create(
                country=country,
                name=rule_data["name"],
                defaults={
                    "rule_type": rule_data["rule_type"],
                    "conditions": rule_data["conditions"],
                    "tax_rate_override": rule_data["tax_rate_override"],
                    "is_active": True,
                    "priority": 10,
                },
            )
            if created:
                rules_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded {created_count} profiles, {rates_created} rates, {rules_created} rules."
        ))
