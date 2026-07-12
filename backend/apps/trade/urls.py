from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TradeDocViewSet

router = DefaultRouter()
router.register(r"documents", TradeDocViewSet, basename="trade-doc")

urlpatterns = [path("", include(router.urls))]
