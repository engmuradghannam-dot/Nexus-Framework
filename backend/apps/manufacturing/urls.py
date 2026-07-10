from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BOMItemViewSet, BOMViewSet, WorkOrderViewSet

router = DefaultRouter()
router.register(r"boms", BOMViewSet)
router.register(r"bom-items", BOMItemViewSet)
router.register(r"work-orders", WorkOrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
