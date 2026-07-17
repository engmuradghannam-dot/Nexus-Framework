from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin

from .models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchasePayment,
    PurchaseTaxCharge,
    Supplier,
)
from .serializers import (
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
    PurchasePaymentSerializer,
    PurchaseTaxChargeSerializer,
    SupplierSerializer,
)


class SupplierViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "email", "tax_id"]
    filterset_fields = ["company", "is_active"]
    company_field = "company"


class PurchaseOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["po_number", "supplier__name"]
    filterset_fields = ["status", "company", "supplier"]
    company_field = "company"
    @action(detail=True, methods=["post"])
    def create_invoice(self, request, pk=None):
        """Generate a draft Purchase Invoice from this order, carrying every line
        item across instead of making the user re-type them."""
        from apps.invoicing.models import Invoice
        from apps.invoicing.serializers import InvoiceSerializer

        order = self.get_object()
        invoice_number = request.data.get("invoice_number")
        invoice_date = request.data.get("invoice_date") or order.transaction_date
        if not invoice_number:
            return Response(
                {"detail": "invoice_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            invoice = Invoice.create_from_purchase_order(
                order,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=request.data.get("due_date"),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED
        )


class PurchaseOrderItemViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    filterset_fields = ["purchase_order", "item"]
    company_field = "purchase_order__company"
    parent_field = "purchase_order"


class PurchaseTaxChargeViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = PurchaseTaxCharge.objects.all()
    serializer_class = PurchaseTaxChargeSerializer
    filterset_fields = ["purchase_order"]
    company_field = "purchase_order__company"
    parent_field = "purchase_order"


class PurchasePaymentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchasePayment.objects.all()
    serializer_class = PurchasePaymentSerializer
    filterset_fields = ["purchase_order"]
    company_field = "purchase_order__company"
