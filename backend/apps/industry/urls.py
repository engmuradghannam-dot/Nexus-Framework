from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SectorViewSet, CompanyViewSet, MetricViewSet

router = DefaultRouter()
router.register(r'sectors', SectorViewSet, basename='sector')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'metrics', MetricViewSet, basename='metric')

urlpatterns = [
    path('', include(router.urls)),
]
