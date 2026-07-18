from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin

from .models import CommissionRule, CustomerTier, StockReservation  # noqa: F401
from .models import Customer, SalesOrder, SalesOrderItem, SalesPayment, SalesTaxCharge
from .serializers import (  # noqa: F401
    CommissionRuleSerializer,
    CustomerTierSerializer,
    StockReservationSerializer,
)
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
    @action(detail=True, methods=["get"])
    def commission(self, request, pk=None):
        """CRM-CTRL-004: commission at whatever rate Sales configured."""
        order = self.get_object()
        rule = order.commission_rule()
        return Response({
            "so_number": order.so_number,
            "grand_total": str(order.grand_total),
            "rule": str(rule) if rule else None,
            "rate_percent": str(rule.rate_percent) if rule else None,
            "amount": str(order.commission_amount),
        })

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """SAL-RULE-002/004: what this order can commit and what must wait."""
        order = self.get_object()
        rows = []
        for line in order.items.select_related("item"):
            available = (
                line.item.available_qty(order.warehouse, exclude_sales_order=order)
                if order.warehouse else None
            )
            rows.append({
                "item_code": line.item.item_code,
                "ordered": str(line.qty),
                "available": str(available) if available is not None else None,
                "backordered": str(line.backordered_qty),
            })
        return Response({
            "so_number": order.so_number,
            "lines": rows,
            "reservations": order.reservations.count(),
            "backorders": [b.so_number for b in order.backorders.all()],
        })

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


class CustomerTierViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """SAL-RULE-005: Sales enters the tier thresholds here."""

    queryset = CustomerTier.objects.select_related("company")
    serializer_class = CustomerTierSerializer
    company_field = "company"


class CommissionRuleViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """CRM-CTRL-004: Sales enters the commission rates here."""

    queryset = CommissionRule.objects.select_related("company", "sales_person", "tier")
    serializer_class = CommissionRuleSerializer
    company_field = "company"
