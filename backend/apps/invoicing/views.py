from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
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
