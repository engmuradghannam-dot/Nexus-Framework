"""Edge-case tests for credit notes / returns (apps.invoicing.CreditNote).

Covers the reversing ledger posting for both sales and purchase returns,
partial returns, the over-credit guard, the unposted-invoice guard, and
idempotent double-post protection. This is the depth work: an ERP must handle
returns correctly and never let a reversal unbalance the ledger.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Account, JournalEntry
from apps.core.models import CompanyProfile
from apps.invoicing.models import CreditNote, Invoice


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Returns Co", code="RET-CO")


@pytest.fixture
def coa(company):
    numbers = {
        "1300": ("Accounts Receivable", "Asset"), "4100": ("Sales Revenue", "Income"),
        "2200": ("VAT Payable", "Liability"), "1400": ("Inventory", "Asset"),
        "2100": ("Accounts Payable", "Liability"),
    }
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in numbers.items()}


def _posted_invoice(company, itype="sales", subtotal=1000, num="INV-R-1"):
    inv = Invoice.objects.create(company=company, invoice_type=itype, invoice_number=num,
                                 party_name="Party", invoice_date=date(2026, 1, 1),
                                 subtotal=subtotal, tax_rate=15)
    ok, _ = inv.post_to_ledger()
    assert ok
    return inv


def _cn(inv, subtotal, num, tax=None):
    tax = Decimal(str(subtotal)) * Decimal("0.15") if tax is None else Decimal(str(tax))
    return CreditNote.objects.create(company=inv.company, original_invoice=inv,
                                     credit_number=num, credit_date=date(2026, 1, 2),
                                     subtotal=subtotal, tax_amount=tax)


@pytest.mark.django_db
class TestCreditNoteSalesReturn:
    def test_full_sales_return_reverses_ledger_balanced(self, company, coa):
        inv = _posted_invoice(company)
        cn = _cn(inv, 1000, "CN-1")
        ok, msg = cn.post_to_ledger()
        assert ok and cn.status == "posted"
        entries = JournalEntry.objects.filter(entry_number__startswith="CN-CN-1")
        # two reversing legs: Sales->AR (1000) and VAT->AR (150)
        assert entries.count() == 2
        total_dr = sum(e.total_debit for e in entries)
        total_cr = sum(e.total_credit for e in entries)
        assert total_dr == total_cr == Decimal("1150.00")   # balanced
        # direction: revenue is debited (reversed), AR credited
        rev_leg = entries.get(entry_number="CN-CN-1-1")
        assert rev_leg.debit_account.account_number == "4100"   # Sales debited
        assert rev_leg.credit_account.account_number == "1300"  # AR credited

    def test_return_type_detected(self, company, coa):
        inv = _posted_invoice(company)
        assert _cn(inv, 100, "CN-RT").return_type == "sales_return"


@pytest.mark.django_db
class TestCreditNotePurchaseReturn:
    def test_purchase_return_reverses_correctly(self, company, coa):
        inv = _posted_invoice(company, itype="purchase", num="PINV-R-1")
        cn = _cn(inv, 500, "CN-P1")
        ok, _ = cn.post_to_ledger()
        assert ok
        leg = JournalEntry.objects.get(entry_number="CN-CN-P1-1")
        # reverse of (Dr Inventory / Cr AP) -> Dr AP / Cr Inventory
        assert leg.debit_account.account_number == "2100"    # AP debited
        assert leg.credit_account.account_number == "1400"   # Inventory credited


@pytest.mark.django_db
class TestPartialAndGuards:
    def test_partial_returns_track_remaining(self, company, coa):
        inv = _posted_invoice(company, subtotal=1000)      # total 1150
        assert inv.creditable_remaining == Decimal("1150.00")
        _cn(inv, 400, "CN-PA").post_to_ledger()            # credit 460 (400+60)
        inv.refresh_from_db()
        assert inv.creditable_remaining == Decimal("690.00")

    def test_over_credit_is_rejected(self, company, coa):
        inv = _posted_invoice(company, subtotal=1000)      # total 1150
        ok, msg = _cn(inv, 1200, "CN-OV").post_to_ledger()  # 1380 > 1150
        assert not ok and "تتجاوز" in msg

    def test_sum_of_partials_cannot_exceed_total(self, company, coa):
        inv = _posted_invoice(company, subtotal=1000)      # total 1150
        _cn(inv, 900, "CN-S1").post_to_ledger()            # 1035 credited
        ok, _ = _cn(inv, 200, "CN-S2").post_to_ledger()    # 230 -> would exceed
        assert not ok

    def test_cannot_credit_unposted_invoice(self, company, coa):
        inv = Invoice.objects.create(company=company, invoice_type="sales",
                                     invoice_number="INV-DRAFT", party_name="P",
                                     invoice_date=date(2026, 1, 1), subtotal=100, tax_rate=15)
        ok, msg = _cn(inv, 50, "CN-U").post_to_ledger()
        assert not ok

    def test_double_post_is_idempotent(self, company, coa):
        inv = _posted_invoice(company)
        cn = _cn(inv, 100, "CN-D")
        assert cn.post_to_ledger()[0] is True
        ok, msg = cn.post_to_ledger()
        assert not ok and "مسبقاً" in msg
        # only one set of entries exists
        assert JournalEntry.objects.filter(entry_number__startswith="CN-CN-D").count() == 2

    def test_clean_rejects_over_credit(self, company, coa):
        inv = _posted_invoice(company, subtotal=1000)
        cn = CreditNote(company=company, original_invoice=inv, credit_number="CN-CL",
                        credit_date=date(2026, 1, 2), subtotal=2000, tax_amount=300)
        with pytest.raises(ValidationError):
            cn.clean()

    def test_zero_amount_rejected(self, company, coa):
        inv = _posted_invoice(company)
        cn = CreditNote(company=company, original_invoice=inv, credit_number="CN-Z",
                        credit_date=date(2026, 1, 2), subtotal=0, tax_amount=0)
        with pytest.raises(ValidationError):
            cn.clean()


@pytest.mark.django_db
class TestCreditNoteAPI:
    def test_create_and_post_via_api(self, company, coa, django_user_model):
        from rest_framework.test import APIClient
        inv = _posted_invoice(company, num="INV-API-Z")
        u = django_user_model.objects.create_superuser(email="cn@nexus.com", password="p12345")
        c = APIClient(); c.force_authenticate(user=u)
        r = c.post("/api/invoicing/credit-notes/", {
            "original_invoice": inv.id, "credit_number": "CN-API-Z", "credit_date": "2026-01-02",
            "subtotal": 1000, "tax_amount": 150, "reason": "return"}, format="json")
        assert r.status_code == 201, r.content
        cnid = r.data["id"]
        r2 = c.post(f"/api/invoicing/credit-notes/{cnid}/post_to_ledger/")
        assert r2.status_code == 200 and r2.data["success"] is True
        # listing filtered by invoice
        r3 = c.get(f"/api/invoicing/credit-notes/?invoice={inv.id}")
        assert r3.data["count"] == 1
        assert r3.data["results"][0]["status"] == "posted"
