from datetime import date
from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice
from .serializers import InvoiceSerializer
from apps.tenants.mixins import TenantScopedMixin


class InvoiceViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["invoice_type", "status"]

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
        company = Company.objects.order_by("id").first()
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
        invoice.paid_amount = (invoice.paid_amount or 0) + amount
        if invoice.paid_amount > invoice.total:
            invoice.paid_amount = invoice.total
        invoice.save(update_fields=["paid_amount"])
        return Response({"success": True, "message": "تم تسجيل الدفعة",
                         "invoice": self.get_serializer(invoice).data})

    @action(detail=False, methods=["get"])
    def aging(self, request):
        """A/R (sales) or A/P (purchase) aging by days overdue."""
        itype = request.query_params.get("type", "sales")
        today = date.today()
        invoices = Invoice.objects.filter(invoice_type=itype).exclude(status="cancelled")
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
