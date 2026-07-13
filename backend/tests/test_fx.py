"""Tests for multi-currency invoices + realized FX gain/loss on payment.

Depth: a foreign-currency invoice posts to the ledger in the base currency at
the invoice-date rate; paying later at a different rate books a realized FX
gain or loss, and the ledger stays balanced in every case.
"""
from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.models import Account, JournalEntry
from apps.core.models import CompanyProfile
from apps.invoicing.models import Invoice, Payment


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="FX Co", code="FX-CO")


@pytest.fixture
def coa(company):
    nums = {"1100": ("Cash", "Asset"), "1200": ("Bank", "Asset"), "1300": ("A/R", "Asset"),
            "2100": ("A/P", "Liability"), "4100": ("Sales", "Income"), "1400": ("Inv", "Asset"),
            "2200": ("VAT", "Liability"), "4900": ("FX Gain", "Income"), "5900": ("FX Loss", "Expense")}
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in nums.items()}


def _fx_invoice(company, rate="3.75", itype="sales", num="INV-FX-1"):
    inv = Invoice.objects.create(company=company, invoice_type=itype, invoice_number=num,
                                 party_name="P", invoice_date=date(2026, 2, 1),
                                 subtotal=1000, tax_rate=15, currency="USD",
                                 exchange_rate=Decimal(rate))
    assert inv.post_to_ledger()[0]
    return inv


def _entries(num):
    return JournalEntry.objects.filter(entry_number__startswith=f"PAY-{num}")


@pytest.mark.django_db
class TestForeignInvoicePosting:
    def test_posts_base_currency_amounts(self, company, coa):
        inv = _fx_invoice(company)                       # 1000 USD @ 3.75
        ar = Account.objects.get(pk=coa["1300"].pk)
        # A/R booked at base = (1000 + 150) * 3.75 = 4312.50
        assert ar.balance == Decimal("4312.50")
        assert inv.base_total == Decimal("4312.50")
        assert inv.is_foreign is True


@pytest.mark.django_db
class TestPaymentFX:
    def test_same_rate_no_fx(self, company, coa):
        inv = _fx_invoice(company, num="INV-FX-SAME")
        Payment.objects.create(invoice=inv, amount=Decimal("1150"), payment_date=date(2026, 2, 10),
                               method="bank", exchange_rate=Decimal("3.75")).post_to_ledger()
        assert not _entries("INV-FX-SAME").filter(entry_number__endswith="-fx").exists()

    def test_sales_gain_when_rate_rises(self, company, coa):
        inv = _fx_invoice(company, num="INV-FX-GAIN")
        ok, msg = Payment.objects.create(invoice=inv, amount=Decimal("1150"), payment_date=date(2026, 2, 10),
                                         method="bank", exchange_rate=Decimal("3.80")).post_to_ledger()
        assert ok and "فرق صرف" in msg
        # gain = 1150 * (3.80 - 3.75) = 57.50 credited to FX gain
        assert Account.objects.get(pk=coa["4900"].pk).balance == Decimal("57.50")
        es = _entries("INV-FX-GAIN")
        assert sum(e.total_debit for e in es) == sum(e.total_credit for e in es)  # balanced

    def test_sales_loss_when_rate_falls(self, company, coa):
        inv = _fx_invoice(company, num="INV-FX-LOSS")
        Payment.objects.create(invoice=inv, amount=Decimal("1150"), payment_date=date(2026, 2, 10),
                               method="bank", exchange_rate=Decimal("3.70")).post_to_ledger()
        # loss = 1150 * (3.75 - 3.70) = 57.50 debited to FX loss
        assert Account.objects.get(pk=coa["5900"].pk).balance == Decimal("57.50")
        es = _entries("INV-FX-LOSS")
        assert sum(e.total_debit for e in es) == sum(e.total_credit for e in es)

    def test_purchase_fx_gain(self, company, coa):
        inv = _fx_invoice(company, itype="purchase", num="PINV-FX", rate="3.75")
        # pay at lower rate -> paid less base than the liability -> gain
        Payment.objects.create(invoice=inv, amount=Decimal("1150"), payment_date=date(2026, 2, 10),
                               method="bank", exchange_rate=Decimal("3.70")).post_to_ledger()
        assert Account.objects.get(pk=coa["4900"].pk).balance == Decimal("57.50")
        es = _entries("PINV-FX")
        assert sum(e.total_debit for e in es) == sum(e.total_credit for e in es)

    def test_backward_compatible_sar(self, company, coa):
        # default rate 1 -> behaves exactly like before, single balanced entry
        inv = Invoice.objects.create(company=company, invoice_type="sales", invoice_number="INV-SAR",
                                     party_name="P", invoice_date=date(2026, 2, 1), subtotal=1000, tax_rate=15)
        inv.post_to_ledger()
        Payment.objects.create(invoice=inv, amount=Decimal("500"), payment_date=date(2026, 2, 5),
                               method="cash").post_to_ledger()
        je = JournalEntry.objects.get(entry_number="PAY-INV-SAR-1")
        assert je.amount == Decimal("500") and je.debit_account.account_number == "1100"
        assert not _entries("INV-SAR").filter(entry_number__endswith="-fx").exists()


@pytest.mark.django_db
class TestPaymentFXviaAPI:
    def test_record_payment_applies_fx_rate(self, company, coa, django_user_model):
        from rest_framework.test import APIClient
        inv = _fx_invoice(company, num="INV-FXAPI")
        u = django_user_model.objects.create_superuser(email="fx@n.com", password="p12345")
        c = APIClient(); c.force_authenticate(user=u)
        r = c.post(f"/api/invoicing/invoices/{inv.id}/record_payment/",
                   {"amount": 1150, "method": "bank", "exchange_rate": 3.80}, format="json")
        assert r.status_code == 200 and r.data["success"]
        assert "فرق صرف 57.50" in r.data["message"]
        assert Account.objects.get(pk=coa["4900"].pk).balance == Decimal("57.50")
