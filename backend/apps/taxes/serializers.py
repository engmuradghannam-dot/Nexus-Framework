from rest_framework import serializers

from .models import CountryTaxProfile, TaxCalculation, TaxRate, TaxRule


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = [
            "id", "country", "name", "tax_type", "rate", "description",
            "effective_date", "expiry_date", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaxRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRule
        fields = [
            "id", "country", "name", "rule_type", "description", "conditions",
            "tax_rate_override", "is_active", "priority", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CountryTaxProfileSerializer(serializers.ModelSerializer):
    tax_rates = TaxRateSerializer(many=True, read_only=True)
    tax_rules = TaxRuleSerializer(many=True, read_only=True)
    current_vat_rate = serializers.SerializerMethodField()

    class Meta:
        model = CountryTaxProfile
        fields = [
            "id", "country_code", "country_name", "currency_code", "vat_enabled",
            "vat_standard_rate", "vat_reduced_rate", "vat_zero_rate_enabled",
            "sales_tax_enabled", "sales_tax_rate", "withholding_tax_enabled",
            "withholding_tax_rate", "tax_id_format", "tax_id_example",
            "fiscal_year_start", "fiscal_year_end", "e_invoicing_mandatory",
            "e_invoicing_threshold", "is_active", "created_at", "updated_at",
            "tax_rates", "tax_rules", "current_vat_rate",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_current_vat_rate(self, obj: CountryTaxProfile) -> str:
        if obj.vat_enabled:
            return str(obj.vat_standard_rate)
        return "0.00"


class CountryTaxProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryTaxProfile
        fields = ["id", "country_code", "country_name", "currency_code", "vat_enabled", "is_active"]


class TaxCalculationSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.country_name", read_only=True)

    class Meta:
        model = TaxCalculation
        fields = [
            "id", "country", "country_name", "reference_number", "base_amount",
            "tax_amount", "total_amount", "applied_tax_rates", "customer_vat_id",
            "is_b2b", "transaction_date", "status", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tax_amount", "total_amount", "applied_tax_rates", "created_at", "updated_at"]


class TaxCalculationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxCalculation
        fields = [
            "country", "reference_number", "base_amount",
            "customer_vat_id", "is_b2b", "notes",
        ]

    def create(self, validated_data):
        calc = TaxCalculation(**validated_data)
        calc.calculate()
        calc.save()
        return calc


class TaxCalculatorInputSerializer(serializers.Serializer):
    country_code = serializers.CharField(max_length=2)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_b2b = serializers.BooleanField(default=False)
    customer_vat_id = serializers.CharField(max_length=50, allow_blank=True, required=False)


class TaxCalculatorOutputSerializer(serializers.Serializer):
    country_code = serializers.CharField()
    base_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    applied_rates = serializers.ListField(child=serializers.DictField())
    is_b2b = serializers.BooleanField()
