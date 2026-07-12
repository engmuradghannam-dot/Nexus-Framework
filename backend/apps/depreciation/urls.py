from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DepreciableAssetViewSet

router = DefaultRouter()
router.register(r"assets", DepreciableAssetViewSet, basename="depr-asset")

urlpatterns = [path("", include(router.urls))]
