from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountTypeViewSet, ChartOfAccountsViewSet, JournalEntryViewSet,
    JournalEntryLineViewSet, InvoiceViewSet, InvoiceItemViewSet,
    PaymentViewSet, FinancialReportViewSet
)

router = DefaultRouter()
router.register(r'account-types', AccountTypeViewSet)
router.register(r'chart-of-accounts', ChartOfAccountsViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'journal-lines', JournalEntryLineViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'invoice-items', InvoiceItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'financial-reports', FinancialReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
