from django.db.models import Sum
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin
from apps.tenants.mixins import TenantScopedMixin

from .models import Account, AccountingPeriod, Budget, CostCenter, JournalEntry
from .serializers import (
    AccountingPeriodSerializer,
    AccountSerializer,
    BudgetSerializer,
    CostCenterSerializer,
    JournalEntrySerializer,
)


class AccountViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["root_type", "account_type", "is_group", "is_active"]
    company_field = "company"

    @action(detail=False, methods=["get"])
    def trial_balance(self, request):
        """Every postable (non-group) account's debit/credit balance side
        by side. A healthy ledger always has total_debit == total_credit."""
        qs = self.filter_queryset(self.get_queryset()).filter(is_group=False)
        rows = []
        total_debit = total_credit = 0
        for acc in qs:
            bal = acc.balance
            is_debit_side = (
                acc.root_type or acc.account_type
            ) in Account.DEBIT_INCREASES
            if is_debit_side:
                debit_balance = bal if bal >= 0 else 0
                credit_balance = -bal if bal < 0 else 0
            else:
                credit_balance = bal if bal >= 0 else 0
                debit_balance = -bal if bal < 0 else 0
            total_debit += debit_balance
            total_credit += credit_balance
            rows.append(
                {
                    "account_id": acc.id,
                    "account_number": acc.account_number,
                    "account_name": acc.account_name,
                    "root_type": acc.root_type or acc.account_type,
                    "debit_balance": debit_balance,
                    "credit_balance": credit_balance,
                }
            )
        return Response(
            {
                "rows": rows,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "balanced": total_debit == total_credit,
            }
        )

    @action(detail=False, methods=["get"])
    def financial_statements(self, request):
        """A minimal Income Statement + Balance Sheet computed straight from
        live account balances — no separate reporting model to keep in sync."""
        qs = self.filter_queryset(self.get_queryset()).filter(is_group=False)

        def total_for(root_type):
            return (
                qs.filter(root_type=root_type).aggregate(total=Sum("balance"))["total"]
                or 0
            )

        total_income = total_for("Income")
        total_expense = total_for("Expense")
        net_income = total_income - total_expense

        total_assets = total_for("Asset")
        total_liabilities = total_for("Liability")
        total_equity = (
            total_for("Equity") + net_income
        )  # retained earnings roll into equity

        return Response(
            {
                "income_statement": {
                    "total_income": total_income,
                    "total_expense": total_expense,
                    "net_income": net_income,
                },
                "balance_sheet": {
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "total_equity": total_equity,
                    "balanced": total_assets == (total_liabilities + total_equity),
                },
            }
        )


    @action(detail=True, methods=["get"])
    def general_ledger(self, request, pk=None):
        """All journal lines touching this account, with a running balance."""
        from .models import JournalEntry
        account = self.get_object()
        entries = JournalEntry.objects.filter(
            models.Q(debit_account=account) | models.Q(credit_account=account)
        ).order_by("posting_date", "id")
        debit_side = (account.root_type or account.account_type) in account.DEBIT_INCREASES
        running = 0
        rows = []
        for e in entries:
            d = float(e.amount) if e.debit_account_id == account.id else 0
            c = float(e.amount) if e.credit_account_id == account.id else 0
            running += (d - c) if debit_side else (c - d)
            rows.append({
                "date": e.posting_date, "entry_number": e.entry_number,
                "reference": e.reference, "debit": d, "credit": c,
                "balance": running,
            })
        return Response({
            "account": {"number": account.account_number, "name": account.account_name},
            "rows": rows, "closing_balance": running,
        })


class JournalEntryViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError
        from .models import AccountingPeriod
        pd = serializer.validated_data.get("posting_date")
        company = serializer.validated_data.get("company")
        if AccountingPeriod.is_locked(company, pd):
            raise ValidationError("الفترة المحاسبية مقفلة لهذا التاريخ — لا يمكن الترحيل.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        entry = self.get_object()
        rev, msg = entry.reverse(
            posting_date=request.data.get("posting_date"),
            reference=request.data.get("reference"))
        if rev is None:
            return Response({"success": False, "message": msg}, status=400)
        return Response({"success": True, "message": msg,
                         "reversal": JournalEntrySerializer(rev).data}, status=201)
    company_field = "company"


class CostCenterViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    company_field = "company"


class BudgetViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    filterset_fields = ["fiscal_year", "status", "cost_center", "account"]
    company_field = "company"


class AccountingPeriodViewSet(TenantScopedMixin, CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = AccountingPeriod.objects.all()
    serializer_class = AccountingPeriodSerializer

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        period = self.get_object()
        period.close()
        return Response({"success": True, "message": f"تم إقفال الفترة {period.name}",
                         "period": self.get_serializer(period).data})

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        period = self.get_object()
        period.reopen()
        return Response({"success": True, "message": f"تم فتح الفترة {period.name}",
                         "period": self.get_serializer(period).data})
