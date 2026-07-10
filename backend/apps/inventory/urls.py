from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ItemBatchViewSet,
    ItemGroupViewSet,
    ItemSerialNumberViewSet,
    ItemViewSet,
    StockEntryViewSet,
    StockReconciliationViewSet,
)

router = DefaultRouter()
router.register(r"item-groups", ItemGroupViewSet)
router.register(r"items", ItemViewSet)
router.register(r"serial-numbers", ItemSerialNumberViewSet)
router.register(r"batches", ItemBatchViewSet)
router.register(r"stock-entries", StockEntryViewSet)
router.register(r"stock-reconciliations", StockReconciliationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
