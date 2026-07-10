from django.contrib import admin

from .models import CountryTaxProfile, TaxCalculation, TaxRate, TaxRule


class TaxRateInline(admin.TabularInline):
    model = TaxRate
    extra = 1
    fields = ["name", "tax_type", "rate", "effective_date", "expiry_date", "is_active"]


class TaxRuleInline(admin.TabularInline):
    model = TaxRule
    extra = 1
    fields = ["name", "rule_type", "priority", "is_active"]


@admin.register(CountryTaxProfile)
class CountryTaxProfileAdmin(admin.ModelAdmin):
    list_display = [
        "country_code", "country_name", "currency_code", "vat_enabled",
        "vat_standard_rate", "sales_tax_enabled", "is_active", "updated_at",
    ]
    list_filter = ["vat_enabled", "sales_tax_enabled", "is_active"]
    search_fields = ["country_code", "country_name"]
    inlines = [TaxRateInline, TaxRuleInline]


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "tax_type", "rate", "effective_date", "is_active"]
    list_filter = ["tax_type", "is_active", "country"]
    search_fields = ["name", "country__country_name"]


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "rule_type", "priority", "is_active"]
    list_filter = ["rule_type", "is_active", "country"]
    search_fields = ["name", "country__country_name"]


@admin.register(TaxCalculation)
class TaxCalculationAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "country", "base_amount", "tax_amount", "total_amount", "status", "created_at"]
    list_filter = ["status", "is_b2b", "country"]
    search_fields = ["reference_number", "customer_vat_id"]
    readonly_fields = ["tax_amount", "total_amount", "applied_tax_rates", "created_at", "updated_at"]
