from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LeadScoringRuleViewSet, LeadViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r"leads", LeadViewSet)
router.register(r"lead-scoring-rules", LeadScoringRuleViewSet)
router.register(r"opportunities", OpportunityViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
