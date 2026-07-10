from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ComplianceCheckViewSet, RegulationViewSet, RiskViewSet

router = DefaultRouter()
router.register(r"regulations", RegulationViewSet, basename="regulation")
router.register(
    r"compliance-checks", ComplianceCheckViewSet, basename="compliancecheck"
)
router.register(r"risks", RiskViewSet, basename="risk")

urlpatterns = [
    path("", include(router.urls)),
]
