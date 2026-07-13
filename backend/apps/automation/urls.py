from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ScheduledJobViewSet, WebhookDeliveryViewSet, WebhookViewSet

router = DefaultRouter()
router.register(r"jobs", ScheduledJobViewSet, basename="scheduled-job")
router.register(r"webhooks", WebhookViewSet, basename="webhook")
router.register(r"deliveries", WebhookDeliveryViewSet, basename="webhook-delivery")

urlpatterns = [path("", include(router.urls))]
