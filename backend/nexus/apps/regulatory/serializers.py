from rest_framework import serializers
from .models import Regulation, ComplianceCheck

class RegulationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Regulation
        fields = '__all__'

    def validate(self, attrs):
        effective_date = attrs.get('effective_date', getattr(self.instance, 'effective_date', None))
        expiry_date = attrs.get('expiry_date', getattr(self.instance, 'expiry_date', None))
        if effective_date and expiry_date and expiry_date < effective_date:
            raise serializers.ValidationError('Expiry date must be on or after the effective date')
        return attrs

class ComplianceCheckSerializer(serializers.ModelSerializer):
    regulation_title = serializers.CharField(source='regulation.title', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.username', read_only=True)

    class Meta:
        model = ComplianceCheck
        fields = '__all__'
