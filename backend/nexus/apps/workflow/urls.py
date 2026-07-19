from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowViewSet, WorkflowStepViewSet,
    ApprovalRequestViewSet, ApprovalActionViewSet
)

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet)
router.register(r'workflow-steps', WorkflowStepViewSet)
router.register(r'approval-requests', ApprovalRequestViewSet)
router.register(r'approval-actions', ApprovalActionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
