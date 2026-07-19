from decimal import Decimal

from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User

from nexus.apps.core.models import Company, Branch
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import alphanumeric_validator

class AccountType(models.Model):
    CATEGORY_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=20, unique=True, validators=[alphanumeric_validator])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class ChartOfAccounts(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='chart_of_accounts')
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, validators=[alphanumeric_validator])
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_bank_account = models.BooleanField(default=False)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'code']
        verbose_name_plural = 'Chart of Accounts'

    def __str__(self):
        return f"{self.code} - {self.name}"

class JournalEntry(models.Model):
    """GL document header - SAP FI Belegkopf (CDHDR-tracked via the audit app)."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('reversed', 'Reversed'),
    ]

    entry_number = models.CharField(max_length=50, unique=True, blank=True)  # JE-YYYY-#####
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField()
    reference = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-entry_number']

    def save(self, *args, **kwargs):
        if not self.entry_number:
            self.entry_number = generate_code(JournalEntry, 'entry_number', 'JE')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"JE-{self.entry_number}"

    @property
    def is_balanced(self):
        # GL document integrity: debits must equal credits (SAP FB50/FB01 check)
        line_debit = sum((line.debit for line in self.lines.all()), Decimal('0.00'))
        line_credit = sum((line.credit for line in self.lines.all()), Decimal('0.00'))
        return line_debit == line_credit

    def post(self):
        """Post the journal entry, enforcing the balance check before status change."""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        if not self.is_balanced:
            raise ValidationError('Debits and credits must balance before posting')
        self.status = 'posted'
        self.posted_at = timezone.now()
        self.save(update_fields=['status', 'posted_at'])

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, related_name='journal_lines')
    description = models.TextField(blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.account.name} - Dr:{self.debit} Cr:{self.credit}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # SAP GL line convention: a line posts to either the debit or the
        # credit side, never both.
        if self.debit and self.credit:
            raise ValidationError('A journal line cannot have both a debit and a credit amount')
        if not self.debit and not self.credit:
            raise ValidationError('A journal line must have a debit or a credit amount')

class Invoice(models.Model):
    TYPE_CHOICES = [
        ('sales', 'Sales Invoice'),
        ('purchase', 'Purchase Invoice'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)  # INV-YYYY-#####
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    customer_name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    customer_email = models.EmailField(blank=True)
    date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    balance_due = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-invoice_number']

    def __str__(self):
        return f"INV-{self.invoice_number}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.due_date and self.date and self.due_date < self.date:
            raise ValidationError('Due date must be on or after the invoice date')

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_code(Invoice, 'invoice_number', 'INV')
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount - self.discount
        self.balance_due = self.total - self.amount_paid
        if self.balance_due <= 0 and self.status not in ['cancelled']:
            self.status = 'paid'
        elif self.due_date and self.due_date < __import__('datetime').date.today() and self.status == 'sent':
            self.status = 'overdue'
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('digital', 'Digital Wallet'),
    ]

    payment_number = models.CharField(max_length=50, unique=True, blank=True)  # PAY-YYYY-#####
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = generate_code(Payment, 'payment_number', 'PAY')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PAY-{self.payment_number}"

class FinancialReport(models.Model):
    REPORT_TYPES = [
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement'),
        ('cash_flow', 'Cash Flow Statement'),
        ('trial_balance', 'Trial Balance'),
        ('general_ledger', 'General Ledger'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_reports')
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    period_start = models.DateField()
    period_end = models.DateField()
    data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.name} ({self.period_start} - {self.period_end})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError('Period end must be on or after period start')
