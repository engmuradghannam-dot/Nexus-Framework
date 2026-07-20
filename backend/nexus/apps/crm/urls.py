from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContactViewSet, CustomerInteractionViewSet, CustomerViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'interactions', CustomerInteractionViewSet)
router.register(r'opportunities', OpportunityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
