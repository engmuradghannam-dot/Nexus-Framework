from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIModelViewSet, PredictionViewSet, InsightViewSet

router = DefaultRouter()
router.register(r'models', AIModelViewSet, basename='aimodel')
router.register(r'predictions', PredictionViewSet, basename='prediction')
router.register(r'insights', InsightViewSet, basename='insight')

urlpatterns = [
    path('', include(router.urls)),
]
