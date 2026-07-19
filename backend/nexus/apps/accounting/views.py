from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
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
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [IsAuthenticated]

class ChartOfAccountsViewSet(viewsets.ModelViewSet):
    queryset = ChartOfAccounts.objects.all()
    serializer_class = ChartOfAccountsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            accounts = ChartOfAccounts.objects.filter(company_id=company_id)
            serializer = self.get_serializer(accounts, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category = request.query_params.get('category')
        if category:
            accounts = ChartOfAccounts.objects.filter(account_type__category=category)
            serializer = self.get_serializer(accounts, many=True)
            return Response(serializer.data)
        return Response({"error": "category required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        company_id = request.query_params.get('company_id')
        accounts = ChartOfAccounts.objects.filter(company_id=company_id) if company_id else ChartOfAccounts.objects.all()

        data = []
        for account in accounts:
            lines = JournalEntryLine.objects.filter(account=account, journal_entry__status='posted')
            total_debit = sum(l.debit for l in lines)
            total_credit = sum(l.credit for l in lines)
            data.append({
                'account_code': account.code,
                'account_name': account.name,
                'debit': total_debit,
                'credit': total_credit,
                'balance': total_debit - total_credit
            })
        return Response(data)

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            entries = JournalEntry.objects.filter(company_id=company_id)
            serializer = self.get_serializer(entries, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    by_status = lambda self, request: Response(self.get_serializer(
        JournalEntry.objects.filter(status=request.query_params.get('status')), many=True
    ).data) if request.query_params.get('status') else Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        entry = self.get_object()
        if entry.status != 'draft':
            return Response({"error": "Only draft entries can be posted"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate balance
        total_debit = sum(l.debit for l in entry.lines.all())
        total_credit = sum(l.credit for l in entry.lines.all())
        if total_debit != total_credit:
            return Response({"error": "Journal entry is not balanced"}, status=status.HTTP_400_BAD_REQUEST)

        entry.status = 'posted'
        entry.posted_at = timezone.now()
        entry.total_debit = total_debit
        entry.total_credit = total_credit
        entry.save()

        # Update account balances
        for line in entry.lines.all():
            account = line.account
            account.current_balance += line.debit - line.credit
            account.save()

        return Response({"status": "posted"})

class JournalEntryLineViewSet(viewsets.ModelViewSet):
    queryset = JournalEntryLine.objects.all()
    serializer_class = JournalEntryLineSerializer
    permission_classes = [IsAuthenticated]

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            invoices = Invoice.objects.filter(company_id=company_id)
            serializer = self.get_serializer(invoices, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        from datetime import date
        invoices = Invoice.objects.filter(due_date__lt=date.today(), status__in=['sent', 'draft'])
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        company_id = request.query_params.get('company_id')
        invoices = Invoice.objects.filter(company_id=company_id) if company_id else Invoice.objects.all()

        return Response({
            'total_invoices': invoices.count(),
            'total_sales': sum(i.total for i in invoices.filter(invoice_type='sales')),
            'total_purchases': sum(i.total for i in invoices.filter(invoice_type='purchase')),
            'overdue_count': invoices.filter(status='overdue').count(),
            'overdue_amount': sum(i.balance_due for i in invoices.filter(status='overdue')),
            'paid_amount': sum(i.amount_paid for i in invoices.all()),
        })

class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_invoice(self, request):
        invoice_id = request.query_params.get('invoice_id')
        if invoice_id:
            payments = Payment.objects.filter(invoice_id=invoice_id)
            serializer = self.get_serializer(payments, many=True)
            return Response(serializer.data)
        return Response({"error": "invoice_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        payment = self.get_object()
        payment.status = 'completed'
        payment.save()

        # Update invoice
        if payment.invoice:
            invoice = payment.invoice
            invoice.amount_paid += payment.amount
            invoice.save()

        return Response({"status": "completed"})

class FinancialReportViewSet(viewsets.ModelViewSet):
    queryset = FinancialReport.objects.all()
    serializer_class = FinancialReportSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        company_id = request.data.get('company_id')
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')

        if not all([company_id, report_type, period_start, period_end]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        data = {}

        if report_type == 'balance_sheet':
            accounts = ChartOfAccounts.objects.filter(company_id=company_id)
            data = {
                'assets': sum(a.current_balance for a in accounts.filter(account_type__category='asset')),
                'liabilities': sum(a.current_balance for a in accounts.filter(account_type__category='liability')),
                'equity': sum(a.current_balance for a in accounts.filter(account_type__category='equity')),
            }
            data['total'] = data['assets'] - data['liabilities'] - data['equity']

        elif report_type == 'income_statement':
            accounts = ChartOfAccounts.objects.filter(company_id=company_id)
            data = {
                'revenue': sum(a.current_balance for a in accounts.filter(account_type__category='revenue')),
                'expenses': sum(a.current_balance for a in accounts.filter(account_type__category='expense')),
            }
            data['net_income'] = data['revenue'] - data['expenses']

        report = FinancialReport.objects.create(
            company_id=company_id,
            report_type=report_type,
            name=f"{report_type.replace('_', ' ').title()} - {period_start} to {period_end}",
            period_start=period_start,
            period_end=period_end,
            data=data,
            generated_by=request.user
        )

        serializer = self.get_serializer(report)
        return Response(serializer.data)
