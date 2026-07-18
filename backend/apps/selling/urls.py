from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommissionRuleViewSet,
    CustomerTierViewSet,
    CustomerViewSet,
    SalesOrderItemViewSet,
    SalesOrderViewSet,
    SalesPaymentViewSet,
    SalesTaxChargeViewSet,
)

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"customer-tiers", CustomerTierViewSet)
router.register(r"commission-rules", CommissionRuleViewSet)
router.register(r"sales-orders", SalesOrderViewSet)
router.register(r"sales-order-items", SalesOrderItemViewSet)
router.register(r"sales-tax-charges", SalesTaxChargeViewSet)
router.register(r"sales-payments", SalesPaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
