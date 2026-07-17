from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GoodsReceiptItemViewSet,
    GoodsReceiptViewSet,
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
router.register(r"goods-receipts", GoodsReceiptViewSet)
router.register(r"goods-receipt-items", GoodsReceiptItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
