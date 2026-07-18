from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin

from .models import (
    GoodsReceipt,
    LatePenaltyTerm,
    SupplierScore,
    SupplierScorecard,
    SupplierScorecardCriterion,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchasePayment,
    PurchaseTaxCharge,
    Supplier,
)
from .serializers import (
    GoodsReceiptItemSerializer,
    LatePenaltyTermSerializer,
    SupplierScoreSerializer,
    SupplierScorecardCriterionSerializer,
    SupplierScorecardSerializer,
    PurchaseRequisitionItemSerializer,
    PurchaseRequisitionSerializer,
    GoodsReceiptSerializer,
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

    def perform_create(self, serializer):
        # FIN-CTRL-002 needs to know who raised the PO.
        user = self.request.user if self.request.user.is_authenticated else None
        super().perform_create(serializer)
        if user is not None and serializer.instance.created_by_id is None:
            serializer.instance.created_by = user
            serializer.instance.save(update_fields=["created_by"])

    @action(detail=True, methods=["get"])
    def late_penalty(self, request, pk=None):
        """PRC-RULE-003: penalty under whatever terms Procurement agreed."""
        order = self.get_object()
        return Response({
            "po_number": order.po_number,
            "required_by": order.required_by,
            "days_late": order.days_to_required_by * -1 if order.days_to_required_by else 0,
            "penalty": str(order.late_penalty()),
        })

    @action(detail=True, methods=["get"])
    def three_way_match(self, request, pk=None):
        """PRC-CTRL-001: does this PO agree with its receipts and invoices?"""
        order = self.get_object()
        matched, discrepancies = order.three_way_match()
        return Response({"matched": matched, "discrepancies": discrepancies})

    @action(detail=True, methods=["get"])
    def price_variance(self, request, pk=None):
        """PRC-RULE-004: lines priced more than 10% off the last PO."""
        order = self.get_object()
        findings = order.check_price_variance()
        return Response({"flagged": bool(findings), "findings": findings})
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


class GoodsReceiptViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = GoodsReceipt.objects.all()
    serializer_class = GoodsReceiptSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["grn_number", "purchase_order__po_number"]
    filterset_fields = ["status", "company", "purchase_order"]
    company_field = "company"

    @action(detail=True, methods=["get"])
    def cross_dock(self, request, pk=None):
        """WHS-RULE-003: which inbound lines can skip storage."""
        grn = self.get_object()
        matches = grn.cross_dock_candidates()
        return Response({"candidates": [
            {
                "item_code": line.po_item.item.item_code,
                "sales_order": so.so_number,
                "customer": so.customer.name,
                "qty": str(qty),
            }
            for line, so, qty in matches
        ]})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """INV-CTRL-003: validate against the PO, then post accepted qty to stock."""
        grn = self.get_object()
        try:
            ok, message = grn.submit()
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": ok, "message": message,
                         "goods_receipt": self.get_serializer(grn).data})


class GoodsReceiptItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = GoodsReceiptItem.objects.all()
    serializer_class = GoodsReceiptItemSerializer
    filterset_fields = ["goods_receipt", "po_item"]
    company_field = "goods_receipt__company"


class PurchaseRequisitionViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.select_related("company", "branch")
    serializer_class = PurchaseRequisitionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["pr_number"]
    filterset_fields = ["status", "company"]
    company_field = "company"

    @action(detail=True, methods=["post"])
    def generate_purchase_orders(self, request, pk=None):
        """PRC-RULE-001."""
        pr = self.get_object()
        try:
            created, unsourced = pr.generate_purchase_orders()
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "created": [po.po_number for po in created],
            "unsourced_items": unsourced,
            "status": pr.status,
        })


class PurchaseRequisitionItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseRequisitionItem.objects.select_related("item")
    serializer_class = PurchaseRequisitionItemSerializer
    filterset_fields = ["requisition"]
    company_field = "requisition__company"


class ProcurementAlertViewSet(viewsets.ViewSet):
    """PRC-RULE-002 and PRC-RULE-005 in one place for the procurement desk."""

    def _scope(self, model):
        user = self.request.user
        if not user.is_authenticated:
            return model.objects.none()
        if user.is_superuser:
            return model.objects.all()
        return model.objects.filter(company__in=user.managed_companies.all())

    def list(self, request):
        deliveries = [
            {
                "po_number": po.po_number,
                "supplier": po.supplier.name,
                "required_by": po.required_by,
                "days_remaining": po.days_to_required_by,
                "overdue": po.delivery_overdue,
            }
            for po in self._scope(PurchaseOrder).filter(status="Submitted")
            .select_related("supplier")
            if po.delivery_due_soon
        ]
        contracts = [
            {
                "supplier": s.name,
                "contract_end": s.contract_end,
                "days_remaining": s.days_to_contract_end,
                "expired": s.contract_expired,
            }
            for s in self._scope(Supplier).filter(is_active=True)
            if s.contract_expires_soon
        ]
        return Response({
            "deliveries_due": deliveries,
            "contracts_expiring": contracts,
        })


class SupplierScorecardCriterionViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """PRC-CTRL-003: Procurement enters the criteria and weights here."""

    queryset = SupplierScorecardCriterion.objects.select_related("company")
    serializer_class = SupplierScorecardCriterionSerializer
    company_field = "company"


class SupplierScorecardViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SupplierScorecard.objects.select_related("supplier").prefetch_related("scores")
    serializer_class = SupplierScorecardSerializer
    filterset_fields = ["supplier"]
    company_field = "supplier__company"


class SupplierScoreViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SupplierScore.objects.select_related("criterion")
    serializer_class = SupplierScoreSerializer
    filterset_fields = ["scorecard"]
    company_field = "scorecard__supplier__company"


class LatePenaltyTermViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """PRC-RULE-003: Procurement enters the contractual terms here."""

    queryset = LatePenaltyTerm.objects.select_related("company", "supplier")
    serializer_class = LatePenaltyTermSerializer
    filterset_fields = ["supplier"]
    company_field = "company"
