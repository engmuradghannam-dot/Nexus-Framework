from rest_framework import serializers
from .models import Regulation, ComplianceCheck, Risk


class ComplianceCheckSerializer(serializers.ModelSerializer):
    regulation_code = serializers.CharField(source='regulation.code', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    auditor_name = serializers.CharField(source='auditor.get_full_name', read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = ['id', 'regulation', 'regulation_code', 'branch', 'branch_name',
                  'result', 'score', 'findings', 'auditor', 'auditor_name',
                  'checked_at', 'created_at']


class RiskSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    risk_score = serializers.IntegerField(read_only=True)
    risk_level = serializers.CharField(read_only=True)
    regulation_code = serializers.CharField(source='related_regulation.code', read_only=True)

    class Meta:
        model = Risk
        fields = ['id', 'title', 'description', 'likelihood', 'impact',
                  'risk_score', 'risk_level', 'status', 'mitigation_plan',
                  'owner', 'owner_name', 'related_regulation', 'regulation_code',
                  'created_at']


class RegulationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    days_until_review = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    compliance_check_count = serializers.IntegerField(source='compliance_checks.count', read_only=True)
    risk_count = serializers.IntegerField(source='risks.count', read_only=True)

    class Meta:
        model = Regulation
        fields = ['id', 'title', 'code', 'jurisdiction', 'severity', 'status',
                  'effective_date', 'review_date', 'days_until_review', 'is_overdue',
                  'description', 'document_url', 'created_by', 'created_by_name',
                  'compliance_check_count', 'risk_count',
                  'is_active', 'created_at']
