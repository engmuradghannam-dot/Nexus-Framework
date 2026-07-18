from datetime import date
from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InvoiceItem, CreditNote, Invoice, Payment
from .serializers import InvoiceItemSerializer, CreditNoteSerializer, InvoiceSerializer, PaymentSerializer
from apps.core.mixins import CompanyScopedMixin
from apps.tenants.mixins import TenantScopedMixin


class InvoiceViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["invoice_type", "status"]
    company_field = "company"

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        invoice = self.get_object()
        ok, msg = invoice.void()
        return Response({"success": ok, "message": msg,
                         "invoice": self.get_serializer(invoice).data},
                        status=200 if ok else 400)

    @action(detail=True, methods=["post"])
    def post_to_ledger(self, request, pk=None):
        invoice = self.get_object()
        ok, msg = invoice.post_to_ledger()
        return Response(
            {"success": ok, "message": msg, "invoice": self.get_serializer(invoice).data},
            status=200 if ok else 400,
        )

    @action(detail=True, methods=["get"])
    def zatca_qr(self, request, pk=None):
        """ZATCA Phase-1 QR (base64 TLV) + the fields needed to print the invoice."""
        from datetime import datetime

        from apps.core.models import Company

        from .zatca import zatca_qr_base64

        invoice = self.get_object()
        company = invoice.company or Company.objects.order_by("id").first()
        seller = getattr(company, "name", "") or "Nexus Company"
        vat_number = getattr(company, "vat_number", "") or getattr(company, "tax_number", "") or "300000000000003"
        ts = datetime.combine(invoice.invoice_date, datetime.min.time()).isoformat()
        qr = zatca_qr_base64(seller, vat_number, ts, invoice.total, invoice.tax_amount)
        return Response({
            "qr": qr,
            "seller_name": seller,
            "vat_number": vat_number,
            "timestamp": ts,
            "invoice": self.get_serializer(invoice).data,
        })

    @action(detail=True, methods=["post"])
    def record_payment(self, request, pk=None):
        invoice = self.get_object()
        try:
            amount = Decimal(str(request.data.get("amount", 0)))
        except Exception:
            return Response({"success": False, "message": "مبلغ غير صالح"}, status=400)
        from datetime import date as _date
        pay = Payment.objects.create(
            invoice=invoice, amount=amount,
            payment_date=request.data.get("payment_date") or _date.today(),
            method=request.data.get("method", "bank"),
            reference=request.data.get("reference", ""),
            exchange_rate=(request.data.get("exchange_rate") or invoice.exchange_rate or 1),
            tenant=getattr(request.user, "tenant", None))
        ok, msg = pay.post_to_ledger()
        if not ok:
            pay.delete()
            return Response({"success": False, "message": msg}, status=400)
        invoice.refresh_from_db()
        return Response({"success": True, "message": msg,
                         "payment": PaymentSerializer(pay).data,
                         "invoice": self.get_serializer(invoice).data})

    @action(detail=False, methods=["get"])
    def aging(self, request):
        """A/R (sales) or A/P (purchase) aging by days overdue."""
        itype = request.query_params.get("type", "sales")
        today = date.today()
        invoices = self.filter_queryset(self.get_queryset()).filter(
            invoice_type=itype
        ).exclude(status="cancelled")
        buckets = {"current": Decimal(0), "d1_30": Decimal(0), "d31_60": Decimal(0),
                   "d61_90": Decimal(0), "d90_plus": Decimal(0)}
        parties = {}
        for inv in invoices:
            out = inv.outstanding
            if out <= 0:
                continue
            due = inv.due_date or inv.invoice_date
            overdue = (today - due).days if due else 0
            if overdue <= 0:
                key = "current"
            elif overdue <= 30:
                key = "d1_30"
            elif overdue <= 60:
                key = "d31_60"
            elif overdue <= 90:
                key = "d61_90"
            else:
                key = "d90_plus"
            buckets[key] += out
            pr = parties.setdefault(inv.party_name, {"party": inv.party_name, "current": Decimal(0),
                "d1_30": Decimal(0), "d31_60": Decimal(0), "d61_90": Decimal(0),
                "d90_plus": Decimal(0), "total": Decimal(0)})
            pr[key] += out
            pr["total"] += out
        total = sum(buckets.values())
        return Response({
            "type": itype,
            "as_of": today.isoformat(),
            "buckets": {k: float(v) for k, v in buckets.items()},
            "total_outstanding": float(total),
            "parties": sorted(
                [{k: (float(v) if isinstance(v, Decimal) else v) for k, v in p.items()} for p in parties.values()],
                key=lambda x: x["total"], reverse=True),
        })


class CreditNoteViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    company_field = "company"

    def get_queryset(self):
        qs = super().get_queryset()
        inv = self.request.query_params.get("invoice")
        return qs.filter(original_invoice=inv) if inv else qs

    @action(detail=True, methods=["post"])
    def post_to_ledger(self, request, pk=None):
        cn = self.get_object()
        ok, msg = cn.post_to_ledger()
        return Response({"success": ok, "message": msg,
                         "credit_note": self.get_serializer(cn).data},
                        status=200 if ok else 400)


class PaymentViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    company_field = "invoice__company"

    def get_queryset(self):
        qs = super().get_queryset()
        inv = self.request.query_params.get("invoice")
        return qs.filter(invoice=inv) if inv else qs


class InvoiceItemViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    """Standalone line editing.

    Lines are normally sent nested inside the invoice, but there was no way to
    touch an individual line at all — no endpoint existed. This gives the UI a
    handle on one row without resubmitting the whole document.
    """

    queryset = InvoiceItem.objects.select_related("invoice", "item")
    serializer_class = InvoiceItemSerializer
    filterset_fields = ["invoice"]
    company_field = "invoice__company"
    tenant_field = "invoice__tenant"

    def _assert_editable(self, invoice):
        from rest_framework.exceptions import PermissionDenied

        if invoice and invoice.status != "draft":
            raise PermissionDenied(
                f"Cannot change lines on a {invoice.status} invoice."
            )

    def perform_create(self, serializer):
        self._assert_editable(serializer.validated_data.get("invoice"))
        serializer.save()

    def perform_update(self, serializer):
        self._assert_editable(serializer.instance.invoice)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_editable(instance.invoice)
        instance.delete()
