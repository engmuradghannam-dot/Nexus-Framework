from rest_framework import serializers
from .models import IndustryProject, IndustryMetric


class IndustryMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryMetric
        fields = '__all__'


class IndustryProjectSerializer(serializers.ModelSerializer):
    metrics = IndustryMetricSerializer(many=True, read_only=True)

    class Meta:
        model = IndustryProject
        fields = '__all__'
