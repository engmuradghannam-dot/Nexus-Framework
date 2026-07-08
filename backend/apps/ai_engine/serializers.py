"""AI Engine Serializers"""
from rest_framework import serializers
from .models import (
    AIAgent, AIConversation, AIPrediction, FeatureFlag,
    LicensePackage, DeploymentTemplate, WorkflowTemplate,
    APIIntegration, DataDictionary
)

class AIAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAgent
        fields = '__all__'

class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversation
        fields = '__all__'

class AIPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPrediction
        fields = '__all__'

class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = '__all__'

class LicensePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensePackage
        fields = '__all__'

class DeploymentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentTemplate
        fields = '__all__'

class WorkflowTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplate
        fields = '__all__'

class APIIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIIntegration
        fields = '__all__'

class DataDictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDictionary
        fields = '__all__'
