"""Tests for accounting-period locking (apps.accounts.AccountingPeriod).

Depth/governance: once a period is closed, no posting, payment, credit note,
void, or reversal may land on a date inside it.
"""
from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.models import Account, AccountingPeriod, JournalEntry
from apps.core.models import CompanyProfile
from apps.invoicing.models import CreditNote, Invoice, Payment


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Period Co", code="PER-CO")


@pytest.fixture
def coa(company):
    nums = {"1100": ("Cash", "Asset"), "1200": ("Bank", "Asset"), "1300": ("A/R", "Asset"),
            "2100": ("A/P", "Liability"), "4100": ("Sales", "Income"), "1400": ("Inv", "Asset"),
            "2200": ("VAT", "Liability")}
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in nums.items()}


def _closed_jan(company):
    return AccountingPeriod.objects.create(company=company, name="2026-01",
        start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), status="closed")


@pytest.mark.django_db
class TestPeriodLock:
    def test_is_locked_detects_closed_period(self, company):
        _closed_jan(company)
        assert AccountingPeriod.is_locked(company, date(2026, 1, 15)) is True
        assert AccountingPeriod.is_locked(company, date(2026, 2, 1)) is False

    def test_invoice_posting_blocked_in_closed_period(self, company, coa):
        _closed_jan(company)
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-PL",
                                     party_name="P", invoice_date=date(2026, 1, 10), subtotal=1000, tax_rate=15)
        ok, msg = inv.post_to_ledger()
        assert not ok and "مقفلة" in msg

    def test_invoice_posting_allowed_outside_closed_period(self, company, coa):
        _closed_jan(company)
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-OK",
                                     party_name="P", invoice_date=date(2026, 2, 10), subtotal=1000, tax_rate=15)
        assert inv.post_to_ledger()[0] is True

    def test_payment_blocked_in_closed_period(self, company, coa):
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-PP",
                                     party_name="P", invoice_date=date(2026, 2, 1), subtotal=1000, tax_rate=15)
        inv.post_to_ledger()
        _closed_jan(company)
        pay = Payment.objects.create(invoice=inv, amount=Decimal("100"), payment_date=date(2026, 1, 20), method="cash")
        ok, msg = pay.post_to_ledger()
        assert not ok and "مقفلة" in msg

    def test_credit_note_blocked_in_closed_period(self, company, coa):
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-PC",
                                     party_name="P", invoice_date=date(2026, 2, 1), subtotal=1000, tax_rate=15)
        inv.post_to_ledger()
        _closed_jan(company)
        cn = CreditNote.objects.create(company=company, original_invoice=inv, credit_number="CN-PL",
                                       credit_date=date(2026, 1, 15), subtotal=100, tax_amount=15)
        ok, msg = cn.post_to_ledger()
        assert not ok and "مقفلة" in msg

    def test_reversal_blocked_in_closed_period(self, company, coa):
        je = JournalEntry.objects.create(company=company, entry_number="JE-PL", posting_date=date(2026, 2, 1),
            reference="x", debit_account=coa["1300"], credit_account=coa["4100"],
            amount=Decimal("100"), total_debit=Decimal("100"), total_credit=Decimal("100"))
        _closed_jan(company)
        rev, msg = je.reverse(posting_date=date(2026, 1, 10))
        assert rev is None and "مقفلة" in msg

    def test_reopen_unlocks(self, company, coa):
        period = _closed_jan(company)
        period.reopen()
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-RE",
                                     party_name="P", invoice_date=date(2026, 1, 10), subtotal=1000, tax_rate=15)
        assert inv.post_to_ledger()[0] is True
