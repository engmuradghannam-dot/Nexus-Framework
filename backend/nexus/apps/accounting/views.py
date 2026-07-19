from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count
import uuid

from nexus.apps.api_infra.scoping import CompanyScopedViewSet
from .models import (
    AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine,
    Invoice, InvoiceItem, Payment, FinancialReport
)
from .serializers import (
    AccountTypeSerializer, ChartOfAccountsSerializer, JournalEntrySerializer,
    JournalEntryLineSerializer, InvoiceSerializer, InvoiceItemSerializer,
    PaymentSerializer, FinancialReportSerializer
)


class AccountTypeViewSet(viewsets.ModelViewSet):
    """Shared lookup table — not company-scoped."""
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [IsAuthenticated]


class ChartOfAccountsViewSet(CompanyScopedViewSet):
    queryset = ChartOfAccounts.objects.all()
    serializer_class = ChartOfAccountsSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category = request.query_params.get('category')
        if not category:
            return Response({"error": "category required"}, status=status.HTTP_400_BAD_REQUEST)
        # get_queryset() is already confined to the caller's companies.
        accounts = self.get_queryset().filter(account_type__category=category)
        return Response(self.get_serializer(accounts, many=True).data)

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        # No more .all() fallback: scoped to the user's companies only.
        accounts = self.get_queryset()
        data = []
        for account in accounts:
            lines = JournalEntryLine.objects.filter(
                account=account, journal_entry__status='posted')
            total_debit = sum(l.debit for l in lines)
            total_credit = sum(l.credit for l in lines)
            data.append({
                'account_code': account.code,
                'account_name': account.name,
                'debit': total_debit,
                'credit': total_credit,
                'balance': total_debit - total_credit,
            })
        return Response(data)


class JournalEntryViewSet(CompanyScopedViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        entries = self.get_queryset().filter(status=status_filter)
        return Response(self.get_serializer(entries, many=True).data)

    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        entry = self.get_object()  # object-level scoping enforced by permission
        if entry.status != 'draft':
            return Response({"error": "Only draft entries can be posted"},
                            status=status.HTTP_400_BAD_REQUEST)

        total_debit = sum(l.debit for l in entry.lines.all())
        total_credit = sum(l.credit for l in entry.lines.all())
        if total_debit != total_credit:
            return Response({"error": "Journal entry is not balanced"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Atomic: posting + balance updates must all-or-nothing.
        with transaction.atomic():
            entry.status = 'posted'
            entry.posted_at = timezone.now()
            entry.total_debit = total_debit
            entry.total_credit = total_credit
            entry.save()
            for line in entry.lines.select_related('account'):
                account = line.account
                account.current_balance += line.debit - line.credit
                account.save(update_fields=['current_balance'])

        return Response({"status": "posted"})


class JournalEntryLineViewSet(CompanyScopedViewSet):
    queryset = JournalEntryLine.objects.all()
    serializer_class = JournalEntryLineSerializer
    company_field = "journal_entry__company"


class InvoiceViewSet(CompanyScopedViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        from datetime import date
        invoices = self.get_queryset().filter(
            due_date__lt=date.today(), status__in=['sent', 'draft'])
        return Response(self.get_serializer(invoices, many=True).data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        invoices = self.get_queryset()
        return Response({
            'total_invoices': invoices.count(),
            'total_sales': sum(i.total for i in invoices.filter(invoice_type='sales')),
            'total_purchases': sum(i.total for i in invoices.filter(invoice_type='purchase')),
            'overdue_count': invoices.filter(status='overdue').count(),
            'overdue_amount': sum(i.balance_due for i in invoices.filter(status='overdue')),
            'paid_amount': sum(i.amount_paid for i in invoices),
        })

    @action(detail=False, methods=['post'])
    def recurring_invoice(self, request):
        invoice_id = request.data.get('invoice_id')
        frequency = request.data.get('frequency', 'monthly')
        if not invoice_id:
            return Response({"error": "invoice_id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # scoped: can only recur an invoice in one of the caller's companies
            original = self.get_queryset().get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        from datetime import timedelta
        days = {'monthly': 30, 'quarterly': 90, 'yearly': 365}.get(frequency, 30)
        with transaction.atomic():
            new_invoice = Invoice.objects.create(
                invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
                company=original.company, branch=original.branch,
                invoice_type=original.invoice_type,
                customer_name=original.customer_name,
                customer_email=original.customer_email,
                date=original.date + timedelta(days=days),
                due_date=original.due_date + timedelta(days=days),
                subtotal=original.subtotal, tax_rate=original.tax_rate,
                discount=original.discount, total=original.total,
                notes=f"Recurring invoice ({frequency}) based on {original.invoice_number}",
            )
            for item in original.items.all():
                InvoiceItem.objects.create(
                    invoice=new_invoice, description=item.description,
                    quantity=item.quantity, unit_price=item.unit_price,
                    total=item.total)
        return Response({"status": "created", "invoice": self.get_serializer(new_invoice).data})

    @action(detail=False, methods=['get'])
    def tax_report(self, request):
        from datetime import date
        year = request.query_params.get('year', date.today().year)
        invoices = self.get_queryset().filter(date__year=year)
        total_tax = sum(i.tax_amount for i in invoices)
        total_sales = sum(i.subtotal for i in invoices.filter(invoice_type='sales'))
        total_purchases = sum(i.subtotal for i in invoices.filter(invoice_type='purchase'))
        return Response({
            "year": year,
            "total_tax_collected": total_tax,
            "total_sales": total_sales,
            "total_purchases": total_purchases,
            "taxable_amount": total_sales - total_purchases,
            "tax_by_quarter": [
                {"quarter": f"Q{q}",
                 "tax": sum(i.tax_amount for i in invoices.filter(date__quarter=q))}
                for q in range(1, 5)
            ],
        })


class InvoiceItemViewSet(CompanyScopedViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    company_field = "invoice__company"


class PaymentViewSet(CompanyScopedViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    company_field = "invoice__company"

    @action(detail=False, methods=['get'])
    def by_invoice(self, request):
        invoice_id = request.query_params.get('invoice_id')
        if not invoice_id:
            return Response({"error": "invoice_id required"}, status=status.HTTP_400_BAD_REQUEST)
        payments = self.get_queryset().filter(invoice_id=invoice_id)
        return Response(self.get_serializer(payments, many=True).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        payment = self.get_object()
        with transaction.atomic():
            payment.status = 'completed'
            payment.save(update_fields=['status'])
            if payment.invoice:
                invoice = payment.invoice
                invoice.amount_paid += payment.amount
                invoice.save(update_fields=['amount_paid'])
        return Response({"status": "completed"})

    @action(detail=False, methods=['post'])
    def bank_reconcile(self, request):
        account_id = request.data.get('account_id')
        statement_balance = request.data.get('statement_balance', 0)
        if not account_id:
            return Response({"error": "account_id required"}, status=status.HTTP_400_BAD_REQUEST)
        # scope the account to the caller's companies
        from nexus.apps.api_infra.scoping import user_company_ids
        allowed = user_company_ids(request.user)
        qs = ChartOfAccounts.objects.all()
        if allowed is not None:
            qs = qs.filter(company_id__in=allowed) if allowed else qs.none()
        try:
            account = qs.get(id=account_id)
        except ChartOfAccounts.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        book_balance = account.current_balance
        difference = book_balance - statement_balance
        return Response({
            "account": account.name, "book_balance": book_balance,
            "statement_balance": statement_balance, "difference": difference,
            "reconciled": abs(difference) < 0.01,
        })


class FinancialReportViewSet(CompanyScopedViewSet):
    queryset = FinancialReport.objects.all()
    serializer_class = FinancialReportSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        # company comes from the caller's membership, never trusted from input
        company_id = self.require_company(request.data.get('company_id'))

        if not all([report_type, period_start, period_end]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        accounts = ChartOfAccounts.objects.filter(company_id=company_id)
        data = {}
        if report_type == 'balance_sheet':
            assets = sum(a.current_balance for a in accounts.filter(account_type__category='asset'))
            liabilities = sum(a.current_balance for a in accounts.filter(account_type__category='liability'))
            equity = sum(a.current_balance for a in accounts.filter(account_type__category='equity'))
            # Accounting identity: Assets = Liabilities + Equity; imbalance should be ~0.
            data = {'assets': assets, 'liabilities': liabilities, 'equity': equity,
                    'imbalance': assets - (liabilities + equity)}
        elif report_type == 'income_statement':
            revenue = sum(a.current_balance for a in accounts.filter(account_type__category='revenue'))
            expenses = sum(a.current_balance for a in accounts.filter(account_type__category='expense'))
            data = {'revenue': revenue, 'expenses': expenses, 'net_income': revenue - expenses}

        report = FinancialReport.objects.create(
            company_id=company_id, report_type=report_type,
            name=f"{report_type.replace('_', ' ').title()} - {period_start} to {period_end}",
            period_start=period_start, period_end=period_end,
            data=data, generated_by=request.user)
        return Response(self.get_serializer(report).data)
