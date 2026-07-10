from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIModelViewSet, InsightViewSet, PredictionViewSet

router = DefaultRouter()
router.register(r"models", AIModelViewSet, basename="aimodel")
router.register(r"predictions", PredictionViewSet, basename="prediction")
router.register(r"insights", InsightViewSet, basename="insight")

urlpatterns = [
    path("", include(router.urls)),
]
