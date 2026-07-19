from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebhookViewSet, WebhookDeliveryViewSet, FileUploadViewSet,
    APIRequestLogViewSet, BatchOperationViewSet
)

router = DefaultRouter()
router.register(r'webhooks', WebhookViewSet)
router.register(r'webhook-deliveries', WebhookDeliveryViewSet)
router.register(r'uploads', FileUploadViewSet)
router.register(r'api-logs', APIRequestLogViewSet)
router.register(r'batch-operations', BatchOperationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
