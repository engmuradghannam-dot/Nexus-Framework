from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ItemVariantViewSet, UnitOfMeasureViewSet, UOMConversionViewSet

router = DefaultRouter()
router.register(r"units", UnitOfMeasureViewSet, basename="uom-unit")
router.register(r"conversions", UOMConversionViewSet, basename="uom-conversion")
router.register(r"variants", ItemVariantViewSet, basename="item-variant")

urlpatterns = [path("", include(router.urls))]
