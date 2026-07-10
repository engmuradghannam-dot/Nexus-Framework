from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, BudgetViewSet, CostCenterViewSet, JournalEntryViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet)
router.register(r"journal-entries", JournalEntryViewSet)
router.register(r"cost-centers", CostCenterViewSet)
router.register(r"budgets", BudgetViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
