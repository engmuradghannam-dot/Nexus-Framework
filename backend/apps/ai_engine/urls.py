"""AI Engine URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIAgentViewSet, AIConversationViewSet, AIPredictionViewSet,
    FeatureFlagViewSet, LicensePackageViewSet, DeploymentTemplateViewSet,
    WorkflowTemplateViewSet, APIIntegrationViewSet, DataDictionaryViewSet
)

router = DefaultRouter()
router.register(r'ai-agents', AIAgentViewSet)
router.register(r'ai-conversations', AIConversationViewSet)
router.register(r'ai-predictions', AIPredictionViewSet)
router.register(r'feature-flags', FeatureFlagViewSet)
router.register(r'license-packages', LicensePackageViewSet)
router.register(r'deployment-templates', DeploymentTemplateViewSet)
router.register(r'workflow-templates', WorkflowTemplateViewSet)
router.register(r'api-integrations', APIIntegrationViewSet)
router.register(r'data-dictionary', DataDictionaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
