"""Documents must be creatable with their lines in one request.

Line items could only be written through their own endpoints, one request each,
after the header existed — a three-line invoice took four round trips and left
an orphan header behind if any of them failed. The order serializers didn't
expose their lines at all, in either direction.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item
from apps.invoicing.models import Invoice
from apps.selling.models import Customer, SalesOrder


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    u = django_user_model.objects.create_superuser(email="nest@x.com", password="testpass123")
    api_client.force_authenticate(u)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Nest Co", code="NEST-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="NST-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def item_a(company):
    return Item.objects.create(company=company, item_code="N-1", item_name="Widget", standard_rate=100)


@pytest.fixture
def item_b(company):
    return Item.objects.create(company=company, item_code="N-2", item_name="Gadget", standard_rate=200)


@pytest.mark.django_db
class TestInvoiceLines:
    def test_create_invoice_with_lines_in_one_request(self, auth_client, company, item_a, item_b):
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N1",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [
                {"item": item_a.pk, "qty": "2", "rate": "100", "tax_rate": "15"},
                {"item": item_b.pk, "qty": "1", "rate": "200", "tax_rate": "15"},
            ],
        }, format="json")
        assert r.status_code == 201, r.data
        inv = Invoice.objects.get(invoice_number="INV-N1")
        assert inv.line_items.count() == 2
        assert inv.subtotal == Decimal("400.00")
        assert inv.total == Decimal("460.00")

    def test_lines_come_back_in_the_response(self, auth_client, company, item_a):
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N2",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [{"item": item_a.pk, "qty": "1", "rate": "100"}],
        }, format="json")
        assert len(r.data["line_items"]) == 1

    def test_adding_a_line_by_patch(self, auth_client, company, item_a, item_b):
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N3",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [{"item": item_a.pk, "qty": "1", "rate": "100", "tax_rate": "15"}],
        }, format="json")
        pk = r.data["id"]
        r2 = auth_client.patch(f"/api/invoicing/invoices/{pk}/", {
            "line_items": [
                {"item": item_a.pk, "qty": "1", "rate": "100", "tax_rate": "15"},
                {"item": item_b.pk, "qty": "1", "rate": "200", "tax_rate": "15"},
            ],
        }, format="json")
        assert r2.status_code == 200, r2.data
        inv = Invoice.objects.get(pk=pk)
        assert inv.line_items.count() == 2
        assert inv.total == Decimal("345.00")

    def test_omitting_lines_leaves_them_alone(self, auth_client, company, item_a):
        """A header-only PATCH must not silently wipe the lines."""
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N4",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [{"item": item_a.pk, "qty": "1", "rate": "100"}],
        }, format="json")
        pk = r.data["id"]
        auth_client.patch(f"/api/invoicing/invoices/{pk}/", {"notes": "hello"}, format="json")
        assert Invoice.objects.get(pk=pk).line_items.count() == 1

    def test_invoice_without_lines_still_allowed(self, auth_client, company):
        """The flat-entry path predates line items and must keep working."""
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N5",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "subtotal": "1000", "tax_rate": "15",
        }, format="json")
        assert r.status_code == 201
        assert Invoice.objects.get(invoice_number="INV-N5").total == Decimal("1150.00")

    def test_standalone_line_endpoint_still_works(self, auth_client, company, item_a):
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N6",
            "party_name": "Acme", "invoice_date": "2026-01-10",
        }, format="json")
        r2 = auth_client.post("/api/invoicing/invoice-items/", {
            "invoice": r.data["id"], "item": item_a.pk, "qty": "3", "rate": "50", "tax_rate": "15",
        }, format="json")
        assert r2.status_code == 201
        assert Invoice.objects.get(pk=r.data["id"]).subtotal == Decimal("150.00")

    def test_a_bad_line_rolls_back_the_whole_document(self, auth_client, company, item_a):
        """No orphan header left behind."""
        r = auth_client.post("/api/invoicing/invoices/", {
            "company": company.pk, "invoice_type": "sales", "invoice_number": "INV-N7",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [
                {"item": item_a.pk, "qty": "1", "rate": "100"},
                {"item": 999999, "qty": "1", "rate": "100"},
            ],
        }, format="json")
        assert r.status_code == 400
        assert not Invoice.objects.filter(invoice_number="INV-N7").exists()


@pytest.mark.django_db
class TestSalesOrderLines:
    def test_create_order_with_lines_in_one_request(
        self, auth_client, company, branch, warehouse, item_a, item_b
    ):
        customer = Customer.objects.create(company=company, name="Acme")
        r = auth_client.post("/api/selling/sales-orders/", {
            "company": company.pk, "customer": customer.pk, "so_number": "SO-N1",
            "transaction_date": "2026-01-10", "branch": branch.pk, "warehouse": warehouse.pk,
            "items": [
                {"item": item_a.pk, "qty": "2", "rate": "100"},
                {"item": item_b.pk, "qty": "1", "rate": "200"},
            ],
        }, format="json")
        assert r.status_code == 201, r.data
        so = SalesOrder.objects.get(so_number="SO-N1")
        assert so.items.count() == 2
        assert so.total_amount == Decimal("400.00")

    def test_lines_are_readable_from_the_order(self, auth_client, company, branch, item_a):
        customer = Customer.objects.create(company=company, name="Acme")
        r = auth_client.post("/api/selling/sales-orders/", {
            "company": company.pk, "customer": customer.pk, "so_number": "SO-N2",
            "transaction_date": "2026-01-10", "branch": branch.pk,
            "items": [{"item": item_a.pk, "qty": "1", "rate": "100"}],
        }, format="json")
        r2 = auth_client.get(f"/api/selling/sales-orders/{r.data['id']}/")
        assert len(r2.data["items"]) == 1
        assert r2.data["items"][0]["item_code"] == "N-1"

    def test_lines_cannot_be_changed_after_submission(
        self, auth_client, company, branch, warehouse, item_a
    ):
        customer = Customer.objects.create(company=company, name="Acme")
        r = auth_client.post("/api/selling/sales-orders/", {
            "company": company.pk, "customer": customer.pk, "so_number": "SO-N3",
            "transaction_date": "2026-01-10", "branch": branch.pk, "warehouse": warehouse.pk,
            "items": [{"item": item_a.pk, "qty": "1", "rate": "100"}],
        }, format="json")
        pk = r.data["id"]
        SalesOrder.objects.filter(pk=pk).update(status="Submitted")
        r2 = auth_client.patch(f"/api/selling/sales-orders/{pk}/", {
            "items": [{"item": item_a.pk, "qty": "99", "rate": "100"}],
        }, format="json")
        assert r2.status_code == 400
        assert SalesOrder.objects.get(pk=pk).items.first().qty == Decimal("1.00")


@pytest.mark.django_db
class TestPurchaseOrderLines:
    def test_create_order_with_lines_in_one_request(
        self, auth_client, company, branch, warehouse, item_a, item_b
    ):
        supplier = Supplier.objects.create(company=company, name="Vendor")
        r = auth_client.post("/api/buying/purchase-orders/", {
            "company": company.pk, "supplier": supplier.pk, "po_number": "PO-N1",
            "transaction_date": "2026-01-10", "branch": branch.pk, "warehouse": warehouse.pk,
            "items": [
                {"item": item_a.pk, "qty": "5", "rate": "80"},
                {"item": item_b.pk, "qty": "2", "rate": "150"},
            ],
        }, format="json")
        assert r.status_code == 201, r.data
        po = PurchaseOrder.objects.get(po_number="PO-N1")
        assert po.items.count() == 2
        assert po.total_amount == Decimal("700.00")

    def test_lines_are_readable_from_the_order(self, auth_client, company, branch, item_a):
        supplier = Supplier.objects.create(company=company, name="Vendor")
        r = auth_client.post("/api/buying/purchase-orders/", {
            "company": company.pk, "supplier": supplier.pk, "po_number": "PO-N2",
            "transaction_date": "2026-01-10", "branch": branch.pk,
            "items": [{"item": item_a.pk, "qty": "1", "rate": "80"}],
        }, format="json")
        r2 = auth_client.get(f"/api/buying/purchase-orders/{r.data['id']}/")
        assert len(r2.data["items"]) == 1
