"""AI Engine Views"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import (
    AIAgent, AIConversation, AIPrediction, FeatureFlag,
    LicensePackage, DeploymentTemplate, WorkflowTemplate,
    APIIntegration, DataDictionary
)
from .serializers import (
    AIAgentSerializer, AIConversationSerializer, AIPredictionSerializer,
    FeatureFlagSerializer, LicensePackageSerializer, DeploymentTemplateSerializer,
    WorkflowTemplateSerializer, APIIntegrationSerializer, DataDictionarySerializer
)

class AIAgentViewSet(viewsets.ModelViewSet):
    queryset = AIAgent.objects.all()
    serializer_class = AIAgentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['industry', 'status', 'is_enabled']
    search_fields = ['name', 'description']

class AIConversationViewSet(viewsets.ModelViewSet):
    queryset = AIConversation.objects.all()
    serializer_class = AIConversationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'user']

class AIPredictionViewSet(viewsets.ModelViewSet):
    queryset = AIPrediction.objects.all()
    serializer_class = AIPredictionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'prediction_type', 'is_actioned']

class FeatureFlagViewSet(viewsets.ModelViewSet):
    queryset = FeatureFlag.objects.all()
    serializer_class = FeatureFlagSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module', 'is_enabled', 'is_premium', 'license_tier']

class LicensePackageViewSet(viewsets.ModelViewSet):
    queryset = LicensePackage.objects.all()
    serializer_class = LicensePackageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tier', 'is_active', 'billing_cycle']

class DeploymentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DeploymentTemplate.objects.all()
    serializer_class = DeploymentTemplateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['industry', 'country', 'company_size']

class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']

class APIIntegrationViewSet(viewsets.ModelViewSet):
    queryset = APIIntegration.objects.all()
    serializer_class = APIIntegrationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['integration_type', 'status', 'is_active']

class DataDictionaryViewSet(viewsets.ModelViewSet):
    queryset = DataDictionary.objects.all()
    serializer_class = DataDictionarySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['module', 'entity_name', 'is_active']
    search_fields = ['entity_name', 'field_name']
