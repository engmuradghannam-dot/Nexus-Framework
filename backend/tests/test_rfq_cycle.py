"""The full sourcing cycle: RFQ → supplier quotations → compare → award → PO.

Modelled on the standard procurement flow (Odoo/SAP): one RFQ goes to several
suppliers, each returns a quote with its own price, lead time and terms, the
buyer compares them on TOTAL cost — not unit price alone — and the winning quote
becomes a draft purchase order. Buying previously started at the PO, so the
sourcing and the competition between suppliers happened outside the system.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, RFQ, Supplier, SupplierQuotation
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item


@pytest.fixture
def company(django_user_model):
    u = django_user_model.objects.create_superuser(email="rfq@x.com", password="x")
    return CompanyProfile.objects.create(name="RFQ Co", code="RFQ-CO", super_admin=u)


@pytest.fixture
def auth_client(db, company):
    c = APIClient()
    c.force_authenticate(company.super_admin)
    return c


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="RFQ-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def items(company):
    return (
        Item.objects.create(company=company, item_code="STL", item_name="Steel"),
        Item.objects.create(company=company, item_code="BLT", item_name="Bolts"),
    )


@pytest.fixture
def suppliers(company):
    return (
        Supplier.objects.create(company=company, name="Supplier A"),
        Supplier.objects.create(company=company, name="Supplier B"),
    )


@pytest.fixture
def rfq_with_lines(auth_client, company, branch, warehouse, items):
    r = auth_client.post("/api/buying/rfqs/", {
        "company": company.pk, "branch": branch.pk, "warehouse": warehouse.pk,
        "rfq_number": "RFQ-001", "transaction_date": str(date.today()),
        "items": [
            {"item": items[0].pk, "qty": "100"},
            {"item": items[1].pk, "qty": "500"},
        ],
    }, format="json")
    assert r.status_code == 201, r.data
    return r.data


@pytest.mark.django_db
class TestRFQCreation:
    def test_rfq_created_with_lines_in_one_request(self, rfq_with_lines):
        assert len(rfq_with_lines["items"]) == 2

    def test_rfq_starts_draft(self, rfq_with_lines):
        assert rfq_with_lines["status"] == "Draft"


@pytest.mark.django_db
class TestQuotations:
    def _quote(self, client, rfq, supplier, lines, prices, **kw):
        return client.post("/api/buying/supplier-quotations/", {
            "rfq": rfq["id"], "supplier": supplier.pk, "status": "Received",
            "lines": [
                {"rfq_line": lines[0]["id"], "unit_price": prices[0]},
                {"rfq_line": lines[1]["id"], "unit_price": prices[1]},
            ],
            **kw,
        }, format="json")

    def test_supplier_can_submit_a_priced_quote(self, auth_client, rfq_with_lines, suppliers):
        r = self._quote(auth_client, rfq_with_lines, suppliers[0], rfq_with_lines["items"], ["50", "3"])
        assert r.status_code == 201, r.data
        assert Decimal(r.data["total_amount"]) == Decimal("6500")  # 100*50 + 500*3

    def test_unpriced_quote_has_no_total(self, auth_client, rfq_with_lines, suppliers):
        r = auth_client.post("/api/buying/supplier-quotations/", {
            "rfq": rfq_with_lines["id"], "supplier": suppliers[0].pk, "status": "Pending",
        }, format="json")
        assert r.status_code == 201
        assert r.data["total_amount"] is None  # not zero — unpriced

    def test_one_quote_per_supplier(self, auth_client, rfq_with_lines, suppliers):
        self._quote(auth_client, rfq_with_lines, suppliers[0], rfq_with_lines["items"], ["50", "3"])
        r = self._quote(auth_client, rfq_with_lines, suppliers[0], rfq_with_lines["items"], ["40", "2"])
        assert r.status_code == 400  # unique (rfq, supplier)


@pytest.mark.django_db
class TestCompareAndAward:
    def _two_quotes(self, client, rfq, suppliers):
        lines = rfq["items"]
        client.post("/api/buying/supplier-quotations/", {
            "rfq": rfq["id"], "supplier": suppliers[0].pk, "status": "Received",
            "lead_time_days": 7, "payment_terms": "Net 30",
            "lines": [{"rfq_line": lines[0]["id"], "unit_price": "50"},
                      {"rfq_line": lines[1]["id"], "unit_price": "3"}],
        }, format="json")
        r = client.post("/api/buying/supplier-quotations/", {
            "rfq": rfq["id"], "supplier": suppliers[1].pk, "status": "Received",
            "lead_time_days": 30, "payment_terms": "Net 60",
            "lines": [{"rfq_line": lines[0]["id"], "unit_price": "45"},
                      {"rfq_line": lines[1]["id"], "unit_price": "2.5"}],
        }, format="json")
        return r.data["id"]  # supplier B's quote id

    def test_compare_ranks_by_total_and_flags_lowest(self, auth_client, rfq_with_lines, suppliers):
        self._two_quotes(auth_client, rfq_with_lines, suppliers)
        r = auth_client.get(f"/api/buying/rfqs/{rfq_with_lines['id']}/compare/")
        quotes = r.data["quotes"]
        assert len(quotes) == 2
        # B is cheapest total (5750) though slower; it must sort first and be flagged.
        assert quotes[0]["supplier"] == "Supplier B"
        assert quotes[0]["is_lowest_total"] is True
        assert Decimal(quotes[0]["total"]) == Decimal("5750")
        # The comparison exposes lead time and terms, so it isn't unit price alone.
        assert quotes[0]["lead_time_days"] == 30
        assert quotes[1]["lead_time_days"] == 7

    def test_award_raises_a_draft_po_from_the_quote(self, auth_client, rfq_with_lines, suppliers):
        qb = self._two_quotes(auth_client, rfq_with_lines, suppliers)
        r = auth_client.post(f"/api/buying/rfqs/{rfq_with_lines['id']}/award/",
                             {"quotation_id": qb}, format="json")
        assert r.status_code == 200, r.data
        po = PurchaseOrder.objects.get(pk=r.data["purchase_order_id"])
        assert po.supplier.name == "Supplier B"
        assert po.status == "Draft"  # award settles price, not authority to spend
        assert po.items.count() == 2
        assert po.total_amount == Decimal("5750.00")

    def test_rfq_cannot_be_awarded_twice(self, auth_client, rfq_with_lines, suppliers):
        qb = self._two_quotes(auth_client, rfq_with_lines, suppliers)
        auth_client.post(f"/api/buying/rfqs/{rfq_with_lines['id']}/award/",
                         {"quotation_id": qb}, format="json")
        r = auth_client.post(f"/api/buying/rfqs/{rfq_with_lines['id']}/award/",
                             {"quotation_id": qb}, format="json")
        assert r.status_code == 400

    def test_awarded_rfq_and_quote_are_marked(self, auth_client, rfq_with_lines, suppliers):
        qb = self._two_quotes(auth_client, rfq_with_lines, suppliers)
        auth_client.post(f"/api/buying/rfqs/{rfq_with_lines['id']}/award/",
                         {"quotation_id": qb}, format="json")
        assert RFQ.objects.get(pk=rfq_with_lines["id"]).status == "Awarded"
        assert SupplierQuotation.objects.get(pk=qb).status == "Awarded"
