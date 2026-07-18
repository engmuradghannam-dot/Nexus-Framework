from decimal import Decimal

from django.db import models

from apps.core.models import Company


class Account(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    ACCOUNT_TYPES = [
        ("Asset", "Asset"),
        ("Liability", "Liability"),
        ("Equity", "Equity"),
        ("Income", "Income"),
        ("Expense", "Expense"),
    ]
    ROOT_TYPES = [
        ("Asset", "Asset"),
        ("Liability", "Liability"),
        ("Equity", "Equity"),
        ("Income", "Income"),
        ("Expense", "Expense"),
    ]
    # Standard accounting convention: Asset/Expense accounts increase with a
    # Debit; Liability/Equity/Income accounts increase with a Credit.
    DEBIT_INCREASES = {"Asset", "Expense"}

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="accounts"
    )
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    root_type = models.CharField(max_length=50, choices=ROOT_TYPES, blank=True)
    parent_account = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    is_group = models.BooleanField(
        default=False,
        help_text="Group accounts are headers that contain child accounts and cannot hold transactions directly.",
    )
    is_bank_account = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="SAR")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def post(self, debit_amount=0, credit_amount=0):
        """Apply a debit/credit to this account's running balance,
        respecting normal accounting sign convention based on root_type."""
        effective_type = self.root_type or self.account_type
        net = (debit_amount or 0) - (credit_amount or 0)
        if effective_type not in self.DEBIT_INCREASES:
            net = -net
        Account.objects.filter(pk=self.pk).update(balance=models.F("balance") + net)
        self.refresh_from_db(fields=["balance"])

    def __str__(self):
        return f"{self.account_number} - {self.account_name}"


# FIN-CTRL-001: entries above this value need two distinct approvers
# (Finance Manager + CFO), on top of the creator.
DUAL_AUTH_THRESHOLD = Decimal("50000")
DUAL_AUTH_ROLES = ["Finance Manager", "CFO"]


class JournalEntry(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    JOURNAL_TYPES = [
        ("Journal Entry", "Journal Entry"),
        ("Bank Entry", "Bank Entry"),
        ("Cash Entry", "Cash Entry"),
        ("Credit Note", "Credit Note"),
        ("Debit Note", "Debit Note"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="journal_entries"
    )
    entry_number = models.CharField(max_length=100, unique=True)
    posting_date = models.DateField()
    reference = models.CharField(max_length=255, blank=True)
    journal_type = models.CharField(
        max_length=50, choices=JOURNAL_TYPES, default="Journal Entry"
    )
    debit_account = models.ForeignKey(
        "Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debit_journal_entries",
        help_text="Quick-entry shortcut for simple two-line postings. Complex postings use JournalEntryLine.",
    )
    credit_account = models.ForeignKey(
        "Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_journal_entries",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="SAR")
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        help_text="Rate to convert `currency` into the company base currency",
    )
    project = models.ForeignKey(
        "pmo.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    cost_center = models.ForeignKey(
        "CostCenter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    branch = models.ForeignKey(
        "core.Branch", on_delete=models.SET_NULL, null=True, blank=True
    )
    posted_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_journal_entries",
    )
    approved_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="journal_entries_approved",
        help_text="First approver. FIN-CTRL-001 requires one above 50,000 SAR.",
    )
    second_approved_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="journal_entries_second_approved",
        help_text="Second, distinct approver required above 50,000 SAR.",
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50,
        default="Draft",
        choices=[("Draft", "Draft"), ("Submitted", "Submitted")],
    )
    notes = models.TextField(blank=True)
    is_reversed = models.BooleanField(default=False)
    reversal_of = models.ForeignKey("self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reversals")
    created_at = models.DateTimeField(auto_now_add=True)

    def check_accounts(self):
        """FIN-RULE-004: both legs must resolve to accounts in THIS company's
        chart of accounts.

        The FK guarantees the account exists; it does not guarantee it is yours.
        A journal entry in company A could name company B's account and post
        against it, corrupting both ledgers across the tenant boundary.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        wrong = []
        for label, account in (
            ("debit_account", self.debit_account),
            ("credit_account", self.credit_account),
        ):
            if account is None:
                continue
            if account.company_id != self.company_id:
                wrong.append(
                    f"{label} '{account.account_number}' belongs to "
                    f"{account.company}, not {self.company}"
                )
        if wrong:
            raise DjangoValidationError(
                f"Account outside this company's chart of accounts: {'; '.join(wrong)}"
            )
        if self.debit_account_id and self.debit_account_id == self.credit_account_id:
            raise DjangoValidationError(
                "Debit and credit cannot be the same account."
            )

    @property
    def needs_dual_authorization(self):
        """FIN-CTRL-001: value above the threshold."""
        return Decimal(self.amount or 0) > DUAL_AUTH_THRESHOLD

    def check_authorization(self):
        """FIN-CTRL-001 (dual authorization) and FIN-CTRL-002 (segregation of
        duties). Both are preventive: they run before the entry posts.

        Below the threshold a single approver distinct from the creator is
        enough; above it two distinct approvers holding Finance Manager and CFO
        authority are required.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.rbac.models import RoleAssignment

        approvers = [a for a in (self.approved_by, self.second_approved_by) if a]
        # FIN-CTRL-002: whoever raised the entry can never be one of its approvers.
        if self.posted_by_id and any(a.pk == self.posted_by_id for a in approvers):
            raise DjangoValidationError(
                "Segregation of duties: the entry's creator cannot approve it."
            )
        if not self.needs_dual_authorization:
            return
        if len(approvers) < 2:
            raise DjangoValidationError(
                f"Entries above {DUAL_AUTH_THRESHOLD} require dual authorization "
                f"({' + '.join(DUAL_AUTH_ROLES)})."
            )
        if approvers[0].pk == approvers[1].pk:
            raise DjangoValidationError(
                "Dual authorization requires two different approvers."
            )
        held = {
            r: [
                a for a in approvers
                if RoleAssignment.objects.filter(user=a, role__name=r).exists()
            ]
            for r in DUAL_AUTH_ROLES
        }
        missing = [r for r, users in held.items() if not users]
        if missing:
            raise DjangoValidationError(
                f"Dual authorization is missing {' and '.join(missing)} approval."
            )
        # One person holding both roles cannot stand in for two people.
        if all(len(u) == 1 for u in held.values()) and \
                held[DUAL_AUTH_ROLES[0]][0].pk == held[DUAL_AUTH_ROLES[1]][0].pk:
            raise DjangoValidationError(
                "Dual authorization requires two different approvers; one user "
                "holding both roles is not sufficient."
            )

    def post_to_ledger(self):
        """Applies this entry's amounts to the real account balances.
        Called exactly once, when the entry transitions to 'Submitted'
        (see JournalEntrySerializer.update). Supports both the simple
        two-account shortcut and full multi-line postings."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        # FIN-RULE-004: nothing posts until both legs are proven to belong to
        # this company's chart of accounts.
        self.check_accounts()

        lines = list(self.lines.all())
        if lines:
            for line in lines:
                if line.account.company_id != self.company_id:
                    raise DjangoValidationError(
                        f"Line account '{line.account.account_number}' belongs to "
                        f"{line.account.company}, not {self.company}."
                    )
            for line in lines:
                if line.account.is_group:
                    raise DjangoValidationError(
                        f"Cannot post to '{line.account}': it is a group account (header), not a postable account."
                    )
            for line in lines:
                line.account.post(debit_amount=line.debit, credit_amount=line.credit)
        elif self.debit_account and self.credit_account:
            if self.debit_account.is_group or self.credit_account.is_group:
                raise DjangoValidationError(
                    "Cannot post to a group account (header) — choose a postable leaf account."
                )
            self.debit_account.post(debit_amount=self.amount)
            self.credit_account.post(credit_amount=self.amount)

    def reverse(self, posting_date=None, reference=None):
        """Create a balanced mirror entry that undoes this one. Idempotent:
        an already-reversed entry (or a reversal entry) cannot be reversed."""
        from datetime import date as _date
        if self.is_reversed:
            return None, "القيد مُعكّس مسبقاً"
        if self.reversal_of_id:
            return None, "لا يمكن عكس قيد عكسي"
        rev_date = posting_date or _date.today()
        if AccountingPeriod.is_locked(self.company, rev_date):
            return None, "الفترة المحاسبية مقفلة لهذا التاريخ"
        rev = JournalEntry.objects.create(
            company=self.company, tenant=self.tenant,
            entry_number=f"REV-{self.entry_number}",
            posting_date=rev_date,
            reference=reference or f"عكس القيد {self.entry_number}",
            debit_account=self.credit_account, credit_account=self.debit_account,
            amount=self.amount, total_debit=self.amount, total_credit=self.amount,
            reversal_of=self,
        )
        # undo the original effect on account balances
        if self.debit_account:
            self.debit_account.post(credit_amount=self.amount)
        if self.credit_account:
            self.credit_account.post(debit_amount=self.amount)
        self.is_reversed = True
        self.save(update_fields=["is_reversed"])
        return rev, "تم عكس القيد"

    def __str__(self):
        return self.entry_number


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.TextField(blank=True)


class CostCenter(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="cost_centers"
    )
    name = models.CharField(max_length=255)
    parent_cost_center = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    STATUS_CHOICES = [("Draft", "Draft"), ("Active", "Active"), ("Closed", "Closed")]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="budgets"
    )
    name = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=20)
    cost_center = models.ForeignKey(
        CostCenter, on_delete=models.SET_NULL, null=True, blank=True
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="budgets"
    )
    budget_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def committed_amount(self):
        """Value of submitted-but-unbilled POs against this budget's cost center.

        actual_amount is a hand-entered figure that nothing in the system ever
        wrote to, so a budget check that only looked at it would pass every PO
        no matter how much was already committed.
        """
        from decimal import Decimal

        from django.db.models import Sum

        from apps.buying.models import PurchaseOrder

        if self.cost_center_id is None:
            return Decimal(0)
        qs = PurchaseOrder.objects.filter(
            cost_center=self.cost_center, status="Submitted",
        )
        if self.start_date and self.end_date:
            qs = qs.filter(transaction_date__range=(self.start_date, self.end_date))
        return qs.aggregate(t=Sum("grand_total"))["t"] or Decimal(0)

    @property
    def available_amount(self):
        """PRC-CTRL-002: what's left to spend."""
        from decimal import Decimal

        return (
            Decimal(self.budget_amount or 0)
            - Decimal(self.actual_amount or 0)
            - self.committed_amount
        )

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


class AccountingPeriod(models.Model):
    """A fiscal period that can be closed to block back-dated postings.

    When a period is 'closed', no journal entry, invoice posting, payment,
    credit note, void, or reversal may post with a date inside it. This is the
    period-lock control every audited ledger needs.
    """

    STATUS = [("open", "Open"), ("closed", "Closed")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    company = models.ForeignKey("core.CompanyProfile", on_delete=models.CASCADE, null=True, blank=True, related_name="accounting_periods")
    name = models.CharField(max_length=80)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=6, choices=STATUS, default="open", db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounting_periods"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @classmethod
    def is_locked(cls, company, on_date):
        """True if on_date falls inside a closed period for this company."""
        if on_date is None:
            return False
        qs = cls.objects.filter(status="closed", start_date__lte=on_date, end_date__gte=on_date)
        if company is not None:
            qs = qs.filter(models.Q(company=company) | models.Q(company__isnull=True))
        return qs.exists()

    def close(self):
        from django.utils import timezone
        self.status = "closed"
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at"])

    def reopen(self):
        self.status = "open"
        self.closed_at = None
        self.save(update_fields=["status", "closed_at"])
