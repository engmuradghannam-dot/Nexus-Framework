from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SalesOrderViewSet, SalesOrderItemViewSet, SalesTaxChargeViewSet, SalesPaymentViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'sales-orders', SalesOrderViewSet)
router.register(r'sales-order-items', SalesOrderItemViewSet)
router.register(r'sales-tax-charges', SalesTaxChargeViewSet)
router.register(r'sales-payments', SalesPaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
