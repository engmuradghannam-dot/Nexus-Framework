"""Pytest tests for the Invoicing module (apps.invoicing).

Covers tax computation, due-date defaulting, ledger posting (sales &
purchase), payment recording, aging buckets, and the ZATCA QR helper —
another revenue-critical module the review report flagged as untested
(P1 #4 follow-up).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Account
from apps.core.models import CompanyProfile
from apps.invoicing.models import Invoice
from apps.invoicing.zatca import zatca_qr_base64


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="billing@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Invoicing Co", code="INV-CO")


@pytest.fixture
def chart_of_accounts(company):
    """Minimal chart matching the account numbers Invoice.post_to_ledger expects."""
    numbers = {
        "1300": ("Accounts Receivable", "Asset"),
        "4100": ("Sales Revenue", "Income"),
        "2200": ("VAT Payable", "Liability"),
        "1400": ("Inventory", "Asset"),
        "2100": ("Accounts Payable", "Liability"),
    }
    accounts = {}
    for number, (name, root) in numbers.items():
        accounts[number] = Account.objects.create(
            company=company,
            account_number=number,
            account_name=name,
            account_type=root,
            root_type=root,
        )
    return accounts


@pytest.mark.django_db
class TestInvoiceComputation:
    def test_recompute_calculates_tax_and_total(self, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-T-001",
            party_name="Client A",
            invoice_date=date(2026, 1, 1),
            subtotal=1000,
            tax_rate=15,
        )
        assert inv.tax_amount == Decimal("150.00")
        assert inv.total == Decimal("1150.00")

    def test_due_date_defaults_to_30_days_after_invoice_date(self, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-T-002",
            party_name="Client B",
            invoice_date=date(2026, 1, 1),
            subtotal=500,
        )
        assert inv.due_date == date(2026, 1, 31)

    def test_explicit_due_date_is_not_overridden(self, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-T-003",
            party_name="Client C",
            invoice_date=date(2026, 1, 1),
            due_date=date(2026, 2, 15),
            subtotal=500,
        )
        assert inv.due_date == date(2026, 2, 15)

    def test_outstanding_is_total_minus_paid(self, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-T-004",
            party_name="Client D",
            invoice_date=date(2026, 1, 1),
            subtotal=1000,
            paid_amount=300,
        )
        assert inv.outstanding == Decimal("850.00")  # total 1150 (1000 + 15% VAT) minus 300 paid


@pytest.mark.django_db
class TestInvoicePostToLedger:
    def test_sales_invoice_posts_balanced_entries(self, chart_of_accounts, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-S-001",
            party_name="Client A",
            invoice_date=date(2026, 1, 1),
            subtotal=1000,
            tax_rate=15,
        )
        ok, msg = inv.post_to_ledger()
        assert ok is True
        inv.refresh_from_db()
        assert inv.status == "posted"

        ar = Account.objects.get(company=company, account_number="1300")
        rev = Account.objects.get(company=company, account_number="4100")
        vat = Account.objects.get(company=company, account_number="2200")
        assert ar.balance == Decimal("1150.00")  # debit side, asset increases with debit
        assert rev.balance == Decimal("1000.00")  # credit side, income increases with credit
        assert vat.balance == Decimal("150.00")

    def test_purchase_invoice_posts_balanced_entries(self, chart_of_accounts, company):
        inv = Invoice.objects.create(
            invoice_type="purchase",
            invoice_number="INV-P-001",
            party_name="Supplier A",
            invoice_date=date(2026, 1, 2),
            subtotal=2000,
            tax_rate=15,
        )
        ok, msg = inv.post_to_ledger()
        assert ok is True

        inventory = Account.objects.get(company=company, account_number="1400")
        ap = Account.objects.get(company=company, account_number="2100")
        vat = Account.objects.get(company=company, account_number="2200")
        assert inventory.balance == Decimal("2000.00")
        # 2200 is a single net-VAT control account: sales credit it (output VAT,
        # a liability), purchases debit it (input VAT, reduces net payable) —
        # so a purchase's tax leg nets negative here, by design.
        assert vat.balance == Decimal("-300.00")
        assert ap.balance == Decimal("2300.00")  # credit side, liability increases with credit

    def test_cannot_post_already_posted_invoice_twice(self, chart_of_accounts, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-S-002",
            party_name="Client B",
            invoice_date=date(2026, 1, 1),
            subtotal=100,
        )
        ok1, _ = inv.post_to_ledger()
        assert ok1 is True
        ok2, msg2 = inv.post_to_ledger()
        assert ok2 is False

    def test_posting_without_chart_of_accounts_fails_gracefully(self, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-S-003",
            party_name="Client C",
            invoice_date=date(2026, 1, 1),
            subtotal=100,
        )
        ok, msg = inv.post_to_ledger()
        assert ok is False
        assert "seed_accounting" in msg

    def test_posts_against_its_own_company_not_the_first_company(self, company):
        # A second, unrelated company with no chart of accounts must not be
        # picked over the invoice's own company (regression test for the
        # "always uses Company.objects.first()" bug found while testing).
        CompanyProfile.objects.create(name="Other Co", code="OTHER-CO")
        for number, name, root in [
            ("1300", "AR", "Asset"), ("4100", "Sales", "Income"), ("2200", "VAT", "Liability"),
        ]:
            Account.objects.create(company=company, account_number=number, account_name=name,
                                    account_type=root, root_type=root)
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-S-004",
            party_name="Client D",
            invoice_date=date(2026, 1, 1),
            subtotal=100,
            company=company,
        )
        ok, msg = inv.post_to_ledger()
        assert ok is True


@pytest.mark.django_db
class TestInvoiceAPI:
    def test_record_payment_caps_at_total(self, auth_client, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-A-001",
            party_name="Client A",
            invoice_date=date(2026, 1, 1),
            subtotal=100,  # total = 115 at 15% tax
        )
        response = auth_client.post(
            f"/api/invoicing/invoices/{inv.id}/record_payment/", {"amount": "9999"}
        )
        assert response.status_code == status.HTTP_200_OK
        inv.refresh_from_db()
        assert inv.paid_amount == inv.total

    def test_post_to_ledger_endpoint(self, auth_client, chart_of_accounts, company):
        inv = Invoice.objects.create(
            invoice_type="sales",
            invoice_number="INV-A-002",
            party_name="Client B",
            invoice_date=date(2026, 1, 1),
            subtotal=200,
        )
        response = auth_client.post(f"/api/invoicing/invoices/{inv.id}/post_to_ledger/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_aging_buckets_current_vs_overdue(self, auth_client, company):
        today = date.today()
        Invoice.objects.create(
            invoice_type="sales", invoice_number="INV-AG-001", party_name="Fresh Co",
            invoice_date=today, due_date=today + timedelta(days=10), subtotal=100,
        )
        Invoice.objects.create(
            invoice_type="sales", invoice_number="INV-AG-002", party_name="Late Co",
            invoice_date=today - timedelta(days=100), due_date=today - timedelta(days=70),
            subtotal=100,
        )
        response = auth_client.get("/api/invoicing/invoices/aging/?type=sales")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["buckets"]["current"] > 0
        assert response.data["buckets"]["d61_90"] > 0

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/invoicing/invoices/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestZatcaQr:
    def test_qr_is_valid_base64_tlv(self):
        qr = zatca_qr_base64("Nexus Co", "300000000000003", "2026-01-01T00:00:00", 1150.0, 150.0)
        import base64
        raw = base64.b64decode(qr)
        # tag=1 (seller), len=len("Nexus Co")=8
        assert raw[0] == 1
        assert raw[1] == len("Nexus Co".encode("utf-8"))
        assert raw[2:2 + raw[1]].decode("utf-8") == "Nexus Co"
