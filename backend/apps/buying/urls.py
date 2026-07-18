from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LatePenaltyTermViewSet,
    SupplierScoreViewSet,
    SupplierScorecardCriterionViewSet,
    SupplierScorecardViewSet,
    GoodsReceiptItemViewSet,
    ProcurementAlertViewSet,
    PurchaseRequisitionItemViewSet,
    PurchaseRequisitionViewSet,
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
router.register(r"purchase-requisitions", PurchaseRequisitionViewSet)
router.register(r"purchase-requisition-items", PurchaseRequisitionItemViewSet)
router.register(r"scorecard-criteria", SupplierScorecardCriterionViewSet)
router.register(r"supplier-scorecards", SupplierScorecardViewSet)
router.register(r"supplier-scores", SupplierScoreViewSet)
router.register(r"late-penalty-terms", LatePenaltyTermViewSet)
router.register(r"alerts", ProcurementAlertViewSet, basename="procurement-alerts")

urlpatterns = [
    path("", include(router.urls)),
]
