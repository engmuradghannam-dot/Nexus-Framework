from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndustryProjectViewSet, IndustryMetricViewSet

router = DefaultRouter()
router.register(r'projects', IndustryProjectViewSet)
router.register(r'metrics', IndustryMetricViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
