from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CreditNoteViewSet, InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"credit-notes", CreditNoteViewSet, basename="credit-note")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [path("", include(router.urls))]
