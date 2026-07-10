"""
Industry Vertical Serializers
"""

from rest_framework import serializers

from .models import Company, IndustryVertical, Metric, Sector, VerticalTemplate


class IndustryVerticalSerializer(serializers.ModelSerializer):
    module_count = serializers.ReadOnlyField()
    feature_count = serializers.ReadOnlyField()
    company_count = serializers.SerializerMethodField()

    class Meta:
        model = IndustryVertical
        fields = [
            "id",
            "name",
            "code",
            "description",
            "modules_enabled",
            "features_config",
            "report_templates",
            "default_currency",
            "supported_currencies",
            "multi_branch_enabled",
            "multi_warehouse_enabled",
            "compliance_frameworks",
            "module_count",
            "feature_count",
            "company_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_company_count(self, obj):
        return obj.companies.count()


class VerticalTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerticalTemplate
        fields = [
            "id",
            "name",
            "vertical_type",
            "description",
            "default_modules",
            "default_features",
            "default_reports",
            "default_compliance",
            "is_active",
            "created_at",
        ]


class SectorSerializer(serializers.ModelSerializer):
    industry_vertical_name = serializers.CharField(
        source="industry_vertical.name", read_only=True
    )

    class Meta:
        model = Sector
        fields = [
            "id",
            "name",
            "code",
            "industry_vertical",
            "industry_vertical_name",
            "description",
            "parent_sector",
            "is_active",
            "created_at",
        ]


class CompanySerializer(serializers.ModelSerializer):
    industry_vertical_name = serializers.CharField(
        source="industry_vertical.name", read_only=True
    )
    effective_modules = serializers.ReadOnlyField()
    effective_features = serializers.ReadOnlyField()
    available_reports = serializers.ReadOnlyField()
    sector_name = serializers.CharField(source="sector.name", read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "ticker",
            "industry_vertical",
            "industry_vertical_name",
            "sector",
            "sector_name",
            "custom_modules",
            "custom_features",
            "market_cap",
            "revenue",
            "employees",
            "headquarters",
            "website",
            "currency",
            "multi_branch_enabled",
            "multi_warehouse_enabled",
            "effective_modules",
            "effective_features",
            "available_reports",
            "is_active",
            "created_at",
            "updated_at",
        ]


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    industry_vertical_name = serializers.CharField(
        source="industry_vertical.name", read_only=True
    )

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "ticker",
            "industry_vertical",
            "industry_vertical_name",
            "is_active",
            "created_at",
        ]


class MetricSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Metric
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "metric_type",
            "value",
            "unit",
            "period",
            "recorded_at",
        ]
