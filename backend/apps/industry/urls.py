"""
Industry Vertical URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndustryVerticalViewSet, VerticalTemplateViewSet,
    CompanyViewSet, SectorViewSet, MetricViewSet
)

router = DefaultRouter()
router.register(r'verticals', IndustryVerticalViewSet, basename='vertical')
router.register(r'templates', VerticalTemplateViewSet, basename='template')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'sectors', SectorViewSet, basename='sector')
router.register(r'metrics', MetricViewSet, basename='metric')

urlpatterns = [
    path('', include(router.urls)),
]
