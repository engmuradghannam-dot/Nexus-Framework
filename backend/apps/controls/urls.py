from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AIAgentViewSet,
    CompanySetupViewSet,
    FormControlViewSet,
    IndustryControlViewSet,
    IndustryViewSet,
    MasterEntityViewSet,
    SectorControlViewSet,
)

router = DefaultRouter()
router.register(r"industries", IndustryViewSet, basename="industry-catalog")
router.register(
    r"industry-controls", IndustryControlViewSet, basename="industry-control"
)
router.register(r"ai-agents", AIAgentViewSet, basename="ai-agent")
router.register(r"master-entities", MasterEntityViewSet, basename="master-entity")
router.register(r"form-controls", FormControlViewSet, basename="form-control")
router.register(r"sector-controls", SectorControlViewSet, basename="sector-control")
router.register(r"company-setup", CompanySetupViewSet, basename="company-setup")

urlpatterns = [
    path("", include(router.urls)),
]
