from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BankAccount, BankTransaction
from .serializers import BankAccountSerializer, BankTransactionSerializer
from apps.tenants.mixins import TenantScopedMixin


class BankAccountViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer


class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["account", "reconciled", "direction"]

    @action(detail=True, methods=["post"])
    def toggle_reconcile(self, request, pk=None):
        t = self.get_object()
        t.reconciled = not t.reconciled
        t.save(update_fields=["reconciled"])
        return Response({"success": True, "reconciled": t.reconciled})
