from django.db import models
from apps.core.models import Company

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('Asset', 'Asset'), ('Liability', 'Liability'), ('Equity', 'Equity'),
        ('Income', 'Income'), ('Expense', 'Expense')
    ]
    ROOT_TYPES = [
        ('Asset', 'Asset'), ('Liability', 'Liability'), ('Equity', 'Equity'),
        ('Income', 'Income'), ('Expense', 'Expense')
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    root_type = models.CharField(max_length=50, choices=ROOT_TYPES, blank=True)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_group = models.BooleanField(default=False, help_text='Group accounts are headers that contain child accounts and cannot hold transactions directly.')
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='SAR')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.account_number} - {self.account_name}"

class JournalEntry(models.Model):
    JOURNAL_TYPES = [
        ('Journal Entry', 'Journal Entry'), ('Bank Entry', 'Bank Entry'),
        ('Cash Entry', 'Cash Entry'), ('Credit Note', 'Credit Note'), ('Debit Note', 'Debit Note'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    entry_number = models.CharField(max_length=100, unique=True)
    posting_date = models.DateField()
    reference = models.CharField(max_length=255, blank=True)
    journal_type = models.CharField(max_length=50, choices=JOURNAL_TYPES, default='Journal Entry')
    debit_account = models.ForeignKey(
        'Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_journal_entries',
        help_text='Quick-entry shortcut for simple two-line postings. Complex postings use JournalEntryLine.'
    )
    credit_account = models.ForeignKey(
        'Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_journal_entries'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='SAR')
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    posted_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_journal_entries')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='Draft', choices=[('Draft', 'Draft'), ('Submitted', 'Submitted')])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.entry_number

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.TextField(blank=True)


class CostCenter(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cost_centers')
    name = models.CharField(max_length=255)
    parent_cost_center = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Active', 'Active'), ('Closed', 'Closed')]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=20)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budgets')
    budget_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def variance(self):
        return self.actual_amount - self.budget_amount

    @property
    def variance_percentage(self):
        if not self.budget_amount:
            return 0
        return (self.variance / self.budget_amount) * 100

    def __str__(self):
        return f"{self.name} ({self.fiscal_year})"
