from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LeadViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r"leads", LeadViewSet)
router.register(r"opportunities", OpportunityViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
