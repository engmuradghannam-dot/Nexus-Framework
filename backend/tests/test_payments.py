"""Edge-case tests for the invoice payment log (apps.invoicing.Payment).

Depth work on A/R & A/P: multiple partial payments with a full audit trail,
correct cash/bank vs AR/AP posting, and no overpayment.
"""
from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.models import Account, JournalEntry
from apps.core.models import CompanyProfile
from apps.invoicing.models import Invoice, Payment


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Pay Co", code="PAY-CO")


@pytest.fixture
def coa(company):
    nums = {"1100": ("Cash", "Asset"), "1200": ("Bank", "Asset"), "1300": ("A/R", "Asset"),
            "2100": ("A/P", "Liability"), "4100": ("Sales", "Income"), "1400": ("Inv", "Asset"),
            "2200": ("VAT", "Liability")}
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in nums.items()}


def _posted(company, itype="sales", subtotal=1000, num="INV-PY-1"):
    inv = Invoice.objects.create(company=company, invoice_type=itype, invoice_number=num,
                                 party_name="P", invoice_date=date(2026, 1, 1),
                                 subtotal=subtotal, tax_rate=15)
    assert inv.post_to_ledger()[0]
    return inv


def _pay(inv, amount, method="bank", num_date=date(2026, 1, 5)):
    return Payment.objects.create(invoice=inv, amount=Decimal(str(amount)),
                                  payment_date=num_date, method=method)


@pytest.mark.django_db
class TestPartialPayments:
    def test_partial_payments_accumulate(self, company, coa):
        inv = _posted(company)                     # total 1150
        assert inv.outstanding == Decimal("1150.00")
        assert _pay(inv, 400).post_to_ledger()[0]
        inv.refresh_from_db()
        assert inv.paid_amount == Decimal("400.00")
        assert inv.outstanding == Decimal("750.00")
        assert _pay(inv, 750).post_to_ledger()[0]
        inv.refresh_from_db()
        assert inv.outstanding == Decimal("0.00")
        assert inv.is_fully_paid is True

    def test_overpayment_rejected(self, company, coa):
        inv = _posted(company)                     # total 1150
        ok, msg = _pay(inv, 2000).post_to_ledger()
        assert not ok and "يتجاوز" in msg

    def test_second_payment_cannot_exceed_remaining(self, company, coa):
        inv = _posted(company)
        _pay(inv, 1000).post_to_ledger()
        ok, msg = _pay(inv, 300).post_to_ledger()   # only 150 left
        assert not ok

    def test_cannot_pay_unposted(self, company, coa):
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-D",
                                     party_name="P", invoice_date=date(2026, 1, 1), subtotal=100, tax_rate=15)
        ok, msg = _pay(inv, 50).post_to_ledger()
        assert not ok


@pytest.mark.django_db
class TestPaymentLedger:
    def test_sales_receipt_posts_cash_and_ar(self, company, coa):
        inv = _posted(company)
        _pay(inv, 500, method="cash").post_to_ledger()
        je = JournalEntry.objects.get(entry_number="PAY-INV-PY-1-1")
        assert je.debit_account.account_number == "1100"   # Cash debited
        assert je.credit_account.account_number == "1300"  # A/R credited
        assert je.amount == Decimal("500")

    def test_bank_method_uses_bank_account(self, company, coa):
        inv = _posted(company, num="INV-BANK")
        _pay(inv, 300, method="bank").post_to_ledger()
        je = JournalEntry.objects.get(entry_number="PAY-INV-BANK-1")
        assert je.debit_account.account_number == "1200"   # Bank debited

    def test_purchase_payment_posts_ap_and_cash(self, company, coa):
        inv = _posted(company, itype="purchase", num="PINV-PY")
        _pay(inv, 500, method="cash").post_to_ledger()
        je = JournalEntry.objects.get(entry_number="PAY-PINV-PY-1")
        assert je.debit_account.account_number == "2100"   # A/P debited
        assert je.credit_account.account_number == "1100"  # Cash credited


@pytest.mark.django_db
class TestPaymentAPI:
    def test_record_payment_creates_log(self, company, coa, django_user_model):
        from rest_framework.test import APIClient
        inv = _posted(company, num="INV-API-PY")
        u = django_user_model.objects.create_superuser(email="pay@n.com", password="p12345")
        c = APIClient(); c.force_authenticate(user=u)
        r = c.post(f"/api/invoicing/invoices/{inv.id}/record_payment/",
                   {"amount": 600, "method": "bank"}, format="json")
        assert r.status_code == 200 and r.data["success"] is True
        # payment logged and listable
        lst = c.get(f"/api/invoicing/payments/?invoice={inv.id}")
        assert lst.data["count"] == 1
        assert lst.data["results"][0]["posted"] is True
        # overpayment via API rejected, no orphan log
        r2 = c.post(f"/api/invoicing/invoices/{inv.id}/record_payment/",
                    {"amount": 9999, "method": "cash"}, format="json")
        assert r2.status_code == 400
        assert c.get(f"/api/invoicing/payments/?invoice={inv.id}").data["count"] == 1
