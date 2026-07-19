from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .ledger_api import LedgerViewSet, LedgerPostingViewSet

from .views import (AccountingPeriodViewSet, AccountViewSet, BudgetViewSet,
                    CostCenterViewSet, JournalEntryViewSet)

router = DefaultRouter()
router.register(r"accounts", AccountViewSet)
router.register(r"journal-entries", JournalEntryViewSet)
router.register(r"cost-centers", CostCenterViewSet)
router.register(r"budgets", BudgetViewSet)
router.register(r"accounting-periods", AccountingPeriodViewSet)
router.register(r"ledgers", LedgerViewSet)
router.register(r"ledger-postings", LedgerPostingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
