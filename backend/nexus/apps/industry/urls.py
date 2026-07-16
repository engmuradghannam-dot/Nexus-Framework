from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndustrySectorViewSet, ProductViewSet, InventoryViewSet,
    SupplierViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet
)

router = DefaultRouter()
router.register(r'sectors', IndustrySectorViewSet)
router.register(r'products', ProductViewSet)
router.register(r'inventory', InventoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-order-items', PurchaseOrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
