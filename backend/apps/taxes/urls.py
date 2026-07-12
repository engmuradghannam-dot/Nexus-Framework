from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CountryTaxProfileViewSet,
    TaxCalculationViewSet,
    TaxRateViewSet,
    TaxRuleViewSet,
    TaxTemplateViewSet,
)

router = DefaultRouter()
router.register(r"profiles", CountryTaxProfileViewSet, basename="tax-profile")
router.register(r"rates", TaxRateViewSet, basename="tax-rate")
router.register(r"rules", TaxRuleViewSet, basename="tax-rule")
router.register(r"calculations", TaxCalculationViewSet, basename="tax-calculation")
router.register(r"templates", TaxTemplateViewSet, basename="tax-template")

urlpatterns = [
    path("", include(router.urls)),
]
