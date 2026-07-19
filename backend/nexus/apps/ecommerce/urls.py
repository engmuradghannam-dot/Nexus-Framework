from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductCatalogViewSet, CustomerViewSet, CartViewSet,
    OrderViewSet, POSessionViewSet, POSTransactionViewSet
)

router = DefaultRouter()
router.register(r'catalog', ProductCatalogViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'carts', CartViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'pos-sessions', POSessionViewSet)
router.register(r'pos-transactions', POSTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
