from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PurchaseOrderItemViewSet,
    PurchaseOrderViewSet,
    PurchasePaymentViewSet,
    PurchaseTaxChargeViewSet,
    SupplierViewSet,
)

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet)
router.register(r"purchase-orders", PurchaseOrderViewSet)
router.register(r"purchase-order-items", PurchaseOrderItemViewSet)
router.register(r"purchase-tax-charges", PurchaseTaxChargeViewSet)
router.register(r"purchase-payments", PurchasePaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
