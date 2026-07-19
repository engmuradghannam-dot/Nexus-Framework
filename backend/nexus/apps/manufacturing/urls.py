from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkCenterViewSet, BOMViewSet, BOMItemViewSet,
    RoutingViewSet, RoutingOperationViewSet,
    ManufacturingOrderViewSet, ManufacturingOrderOperationViewSet,
    MaterialRequisitionViewSet, MaterialRequisitionItemViewSet
)

router = DefaultRouter()
router.register(r'work-centers', WorkCenterViewSet)
router.register(r'boms', BOMViewSet)
router.register(r'bom-items', BOMItemViewSet)
router.register(r'routings', RoutingViewSet)
router.register(r'routing-operations', RoutingOperationViewSet)
router.register(r'manufacturing-orders', ManufacturingOrderViewSet)
router.register(r'manufacturing-operations', ManufacturingOrderOperationViewSet)
router.register(r'material-requisitions', MaterialRequisitionViewSet)
router.register(r'material-requisition-items', MaterialRequisitionItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
