from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CurrencyViewSet

router = DefaultRouter()
router.register(r"currencies", CurrencyViewSet, basename="currency")

urlpatterns = [path("", include(router.urls))]
