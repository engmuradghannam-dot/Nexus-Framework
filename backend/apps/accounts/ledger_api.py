from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin

from .parallel_ledgers import Ledger, LedgerPosting


class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = ["id", "company", "tenant", "code", "name", "standard",
                  "currency", "is_leading", "is_active", "created_at"]
        read_only_fields = ["created_at"]


class LedgerPostingSerializer(serializers.ModelSerializer):
    ledger_code = serializers.CharField(source="ledger.code", read_only=True)
    account_number = serializers.CharField(source="account.account_number", read_only=True)

    class Meta:
        model = LedgerPosting
        fields = ["id", "ledger", "ledger_code", "journal_entry", "account",
                  "account_number", "debit", "credit", "description",
                  "posting_date", "created_at"]
        read_only_fields = ["created_at"]


class LedgerViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Define parallel ledgers (IFRS, local GAAP, tax, management) per company."""

    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    company_field = "company"
    filterset_fields = ["standard", "is_leading", "is_active", "company"]

    @action(detail=True, methods=["get"])
    def trial_balance(self, request, pk=None):
        """This ledger's balance per account — an independent trial balance."""
        from django.db.models import Sum

        ledger = self.get_object()
        rows = (
            ledger.postings.values("account__account_number", "account__account_name")
            .annotate(debit=Sum("debit"), credit=Sum("credit"))
            .order_by("account__account_number")
        )
        return Response({"ledger": ledger.code, "standard": ledger.standard, "rows": list(rows)})


class LedgerPostingViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only postings across ledgers, filterable by ledger and account."""

    queryset = LedgerPosting.objects.select_related("ledger", "account")
    serializer_class = LedgerPostingSerializer
    company_field = "ledger__company"
    filterset_fields = ["ledger", "account", "journal_entry"]
