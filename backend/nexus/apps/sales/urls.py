from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BackorderViewSet, DeliveryViewSet, InvoiceViewSet, QuotationViewSet, SalesOrderItemViewSet, SalesOrderViewSet

router = DefaultRouter()
router.register(r'orders', SalesOrderViewSet)
router.register(r'order-items', SalesOrderItemViewSet)
router.register(r'backorders', BackorderViewSet)
router.register(r'deliveries', DeliveryViewSet)
router.register(r'quotations', QuotationViewSet)
router.register(r'invoices', InvoiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
