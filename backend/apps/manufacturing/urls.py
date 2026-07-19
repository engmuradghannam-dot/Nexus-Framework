from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BOMItemViewSet,
    BOMViewSet,
    JobCardViewSet,
    QualityInspectionParameterViewSet,
    QualityInspectionViewSet,
    WorkOrderViewSet,
    ProductionBatchViewSet,
)

router = DefaultRouter()
router.register(r"boms", BOMViewSet)
router.register(r"bom-items", BOMItemViewSet)
router.register(r"work-orders", WorkOrderViewSet)
router.register(r"job-cards", JobCardViewSet)
router.register(r"quality-inspections", QualityInspectionViewSet)
router.register(r"quality-inspection-parameters", QualityInspectionParameterViewSet)
router.register(r"production-batches", ProductionBatchViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
