from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdvancedSearchViewSet, AggregationAPIViewSet,

    WebhookViewSet, WebhookDeliveryViewSet, FileUploadViewSet,
    APIRequestLogViewSet, BatchOperationViewSet
)
from .tenancy import TenantViewSet, TenantUserViewSet

router = DefaultRouter()
router.register(r'webhooks', WebhookViewSet)
router.register(r'webhook-deliveries', WebhookDeliveryViewSet)
router.register(r'uploads', FileUploadViewSet)
router.register(r'api-logs', APIRequestLogViewSet)
router.register(r'batch-operations', BatchOperationViewSet)
router.register(r'search', AdvancedSearchViewSet, basename='search')
router.register(r'aggregation', AggregationAPIViewSet, basename='aggregation')
router.register(r'tenants', TenantViewSet)
router.register(r'tenant-users', TenantUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
