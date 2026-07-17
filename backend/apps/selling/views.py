from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin

from .models import Customer, SalesOrder, SalesOrderItem, SalesPayment, SalesTaxCharge
from .serializers import (
    CustomerSerializer,
    SalesOrderItemSerializer,
    SalesOrderSerializer,
    SalesPaymentSerializer,
    SalesTaxChargeSerializer,
)


class CustomerViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    company_field = "company"


class SalesOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    company_field = "company"
    @action(detail=True, methods=["post"])
    def create_invoice(self, request, pk=None):
        """Generate a draft Sales Invoice from this order, carrying every line
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
            invoice = Invoice.create_from_sales_order(
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


class SalesOrderItemViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    filterset_fields = ["sales_order", "item"]
    company_field = "sales_order__company"
    parent_field = "sales_order"


class SalesTaxChargeViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = SalesTaxCharge.objects.all()
    serializer_class = SalesTaxChargeSerializer
    filterset_fields = ["sales_order"]
    company_field = "sales_order__company"
    parent_field = "sales_order"


class SalesPaymentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SalesPayment.objects.all()
    serializer_class = SalesPaymentSerializer
    filterset_fields = ["sales_order"]
    company_field = "sales_order__company"
