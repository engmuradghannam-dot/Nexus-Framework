"""Edge-case tests for invoice void and journal-entry reversal.

Depth work on the financial core: a posted document must be reversible without
ever unbalancing the ledger, and reversals must be idempotent and guarded.
"""
from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.models import Account, JournalEntry
from apps.core.models import CompanyProfile
from apps.invoicing.models import CreditNote, Invoice


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Void Co", code="VOID-CO")


@pytest.fixture
def coa(company):
    nums = {"1300": ("A/R", "Asset"), "4100": ("Sales", "Income"), "2200": ("VAT", "Liability"),
            "1400": ("Inventory", "Asset"), "2100": ("A/P", "Liability")}
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in nums.items()}


def _posted(company, itype="sales", subtotal=1000, num="INV-V-1"):
    inv = Invoice.objects.create(company=company, invoice_type=itype, invoice_number=num,
                                 party_name="P", invoice_date=date(2026, 1, 1),
                                 subtotal=subtotal, tax_rate=15)
    assert inv.post_to_ledger()[0]
    return inv


@pytest.mark.django_db
class TestInvoiceVoid:
    def test_void_reverses_ledger_and_cancels(self, company, coa):
        inv = _posted(company)
        ar = coa["1300"]; rev = coa["4100"]
        ar_after_post = Account.objects.get(pk=ar.pk).balance
        rev_after_post = Account.objects.get(pk=rev.pk).balance
        ok, msg = inv.void()
        assert ok and inv.status == "cancelled"
        # reversing entries exist and balance
        ve = JournalEntry.objects.filter(entry_number__startswith="VOID-INV-V-1")
        assert ve.count() == 2
        assert sum(e.total_debit for e in ve) == sum(e.total_credit for e in ve) == Decimal("1150.00")
        # net effect on A/R and Revenue is zeroed out vs pre-post
        assert Account.objects.get(pk=ar.pk).balance == ar_after_post - Decimal("1150.00")
        assert Account.objects.get(pk=rev.pk).balance == rev_after_post - Decimal("1000.00")

    def test_cannot_void_unposted(self, company, coa):
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-UP",
                                     party_name="P", invoice_date=date(2026, 1, 1), subtotal=100, tax_rate=15)
        ok, msg = inv.void()
        assert not ok and "مُرحّلة" in msg

    def test_cannot_void_with_payments(self, company, coa):
        inv = _posted(company, num="INV-PAY")
        inv.paid_amount = Decimal("500"); inv.save(update_fields=["paid_amount"])
        ok, msg = inv.void()
        assert not ok and "دفعات" in msg

    def test_cannot_void_with_posted_credit_note(self, company, coa):
        inv = _posted(company, num="INV-CN")
        cn = CreditNote.objects.create(company=company, original_invoice=inv, credit_number="CN-V1",
                                       credit_date=date(2026, 1, 2), subtotal=100, tax_amount=15)
        assert cn.post_to_ledger()[0]
        ok, msg = inv.void()
        assert not ok and "إشعارات دائنة" in msg


@pytest.mark.django_db
class TestJournalReverse:
    def _entry(self, company, coa, amt=500, num="JE-1"):
        return JournalEntry.objects.create(
            company=company, entry_number=num, posting_date=date(2026, 1, 1),
            reference="manual", debit_account=coa["1300"], credit_account=coa["4100"],
            amount=Decimal(amt), total_debit=Decimal(amt), total_credit=Decimal(amt))

    def test_reverse_creates_balanced_mirror(self, company, coa):
        je = self._entry(company, coa)
        # apply original effect to balances manually (mirrors posting)
        coa["1300"].post(debit_amount=je.amount); coa["4100"].post(credit_amount=je.amount)
        ar0 = Account.objects.get(pk=coa["1300"].pk).balance
        rev, msg = je.reverse()
        assert rev is not None and je.is_reversed is True
        assert rev.debit_account_id == coa["4100"].pk   # swapped
        assert rev.credit_account_id == coa["1300"].pk
        assert rev.total_debit == rev.total_credit == Decimal("500")
        assert rev.reversal_of_id == je.pk
        # A/R balance returns to its pre-entry value
        assert Account.objects.get(pk=coa["1300"].pk).balance == ar0 - Decimal("500")

    def test_cannot_reverse_twice(self, company, coa):
        je = self._entry(company, coa, num="JE-2")
        je.reverse()
        r2, msg = je.reverse()
        assert r2 is None and "مسبقاً" in msg

    def test_cannot_reverse_a_reversal(self, company, coa):
        je = self._entry(company, coa, num="JE-3")
        rev, _ = je.reverse()
        r2, msg = rev.reverse()
        assert r2 is None and "عكسي" in msg
