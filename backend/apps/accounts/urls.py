from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AccountingPeriodViewSet, AccountViewSet, BudgetViewSet,
                    CostCenterViewSet, JournalEntryViewSet)

router = DefaultRouter()
router.register(r"accounts", AccountViewSet)
router.register(r"journal-entries", JournalEntryViewSet)
router.register(r"cost-centers", CostCenterViewSet)
router.register(r"budgets", BudgetViewSet)
router.register(r"accounting-periods", AccountingPeriodViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
