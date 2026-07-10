from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AssetCategoryViewSet, AssetViewSet

router = DefaultRouter()
router.register(r"asset-categories", AssetCategoryViewSet)
router.register(r"assets", AssetViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
