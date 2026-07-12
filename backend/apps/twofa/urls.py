from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TwoFactorViewSet

router = DefaultRouter()
router.register(r"2fa", TwoFactorViewSet, basename="twofa")

urlpatterns = [path("", include(router.urls))]
