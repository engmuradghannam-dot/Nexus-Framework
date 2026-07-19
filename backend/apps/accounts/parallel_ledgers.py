"""Parallel ledgers — simultaneous reporting under multiple accounting standards.

A single business event often has to be reported more than one way: under IFRS
for the group, and under local GAAP (in Saudi, SOCPA-aligned) for the statutory
filing. The two can disagree on the numbers — different depreciation lives,
different revenue timing — even though the underlying transaction is one.

Among the systems Nexus is compared to, only SAP S/4HANA and Oracle Cloud ERP
offer true parallel ledgers; Odoo does not. This adds them as an ADDITIVE layer:
the existing single-ledger posting is untouched and remains the 'leading' path.
A LedgerPosting records how one journal entry lands in one ledger, so the same
entry can carry a different amount per standard, and each ledger reports on its
own.
"""
from decimal import Decimal

from django.db import models


class Ledger(models.Model):
    """One accounting ledger — a lens on the books under a given standard.

    The leading ledger mirrors the existing single-ledger postings; additional
    ledgers (local GAAP, tax, management) coexist alongside it.
    """

    STANDARDS = [
        ("ifrs", "IFRS"),
        ("local_gaap", "Local GAAP (SOCPA)"),
        ("tax", "Tax"),
        ("management", "Management"),
    ]

    company = models.ForeignKey(
        "core.CompanyProfile", on_delete=models.CASCADE, related_name="ledgers"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    standard = models.CharField(max_length=16, choices=STANDARDS)
    currency = models.CharField(max_length=10, default="SAR")
    # Exactly one leading ledger per company — the statutory book of record that
    # the existing posting logic already maintains.
    is_leading = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["company", "-is_leading", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="unique_ledger_code_per_company"),
            models.UniqueConstraint(
                fields=["company"], condition=models.Q(is_leading=True),
                name="one_leading_ledger_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_standard_display()})"

    def balance_for(self, account):
        """This ledger's net balance for an account — sum of its postings,
        independent of any other ledger."""
        agg = self.postings.filter(account=account).aggregate(
            d=models.Sum("debit"), c=models.Sum("credit")
        )
        return (agg["d"] or Decimal("0")) - (agg["c"] or Decimal("0"))


class LedgerPosting(models.Model):
    """How one journal entry lands in one ledger, on one account.

    The same source entry can post different amounts to different ledgers — a
    depreciation charge that differs between IFRS and local GAAP is two postings
    with the same source and different numbers. Keeping them as separate rows is
    what lets each ledger report independently.
    """

    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE, related_name="postings")
    journal_entry = models.ForeignKey(
        "accounts.JournalEntry", on_delete=models.CASCADE,
        related_name="ledger_postings", null=True, blank=True,
    )
    account = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="+")
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)
    posting_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ledger", "posting_date", "id"]
        indexes = [models.Index(fields=["ledger", "account"])]

    def __str__(self):
        return f"{self.ledger.code}: {self.account.account_number} D{self.debit} C{self.credit}"


def post_to_ledgers(company, account, posting_date, debit=0, credit=0,
                    journal_entry=None, description="", ledger_amounts=None):
    """Record a posting across a company's active ledgers.

    By default the same debit/credit lands in every active ledger. When the
    standards disagree, pass ledger_amounts={ledger_code: (debit, credit)} to
    override specific ledgers — e.g. a different depreciation figure under local
    GAAP than under IFRS. Ledgers not named use the default amounts.

    Returns the created LedgerPosting rows.
    """
    ledger_amounts = ledger_amounts or {}
    created = []
    for ledger in Ledger.objects.filter(company=company, is_active=True):
        d, c = ledger_amounts.get(ledger.code, (debit, credit))
        created.append(LedgerPosting.objects.create(
            ledger=ledger, journal_entry=journal_entry, account=account,
            debit=Decimal(d or 0), credit=Decimal(c or 0),
            description=description, posting_date=posting_date,
        ))
    return created
