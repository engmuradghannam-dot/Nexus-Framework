from rest_framework import serializers
from .models import Sector, Company, Metric


class SectorSerializer(serializers.ModelSerializer):
    sub_sector_count = serializers.IntegerField(source='sub_sectors.count', read_only=True)
    company_count = serializers.IntegerField(source='companies.count', read_only=True)

    class Meta:
        model = Sector
        fields = ['id', 'name', 'code', 'description', 'parent_sector',
                  'sub_sector_count', 'company_count', 'is_active', 'created_at']


class MetricSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Metric
        fields = ['id', 'company', 'company_name', 'name', 'metric_type',
                  'value', 'unit', 'period', 'recorded_at']


class CompanySerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    metric_count = serializers.IntegerField(source='metrics.count', read_only=True)
    latest_metrics = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'ticker', 'sector', 'sector_name',
                  'market_cap', 'revenue', 'employees', 'headquarters',
                  'website', 'metric_count', 'latest_metrics',
                  'is_active', 'created_at']

    def get_latest_metrics(self, obj):
        metrics = obj.metrics.all()[:5]
        return MetricSerializer(metrics, many=True).data
