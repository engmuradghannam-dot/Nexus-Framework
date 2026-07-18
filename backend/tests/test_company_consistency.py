"""Writes must not reference another company's records.

CompanyScopedMixin scoped what a user could read. Nothing scoped what they
could reference: DRF resolves a PrimaryKeyRelatedField against the model's
default manager, so a user of company A could POST a sales order naming company
B's customer and B's items. They never needed to see the record — primary keys
are sequential integers. Reading was fail-closed; writing was wide open.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Account, CostCenter
from apps.buying.models import Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.hr.models import Department, Employee
from apps.inventory.models import Item
from apps.selling.models import Customer


@pytest.fixture
def attacker(django_user_model):
    return django_user_model.objects.create_user(email="atk@x.com", password="x")


@pytest.fixture
def alpha(attacker):
    return CompanyProfile.objects.create(name="Alpha", code="ALPHA-X", super_admin=attacker)


@pytest.fixture
def beta():
    return CompanyProfile.objects.create(name="Beta", code="BETA-X")


@pytest.fixture
def client(attacker):
    c = APIClient()
    c.force_authenticate(attacker)
    return c


@pytest.fixture
def a_branch(alpha):
    return Branch.objects.create(company=alpha, name="A", code="A-BR", address="x")


@pytest.fixture
def a_warehouse(a_branch):
    return Warehouse.objects.get(branch=a_branch)


@pytest.fixture
def b_branch(beta):
    return Branch.objects.create(company=beta, name="B", code="B-BR", address="x")


@pytest.fixture
def a_item(alpha):
    return Item.objects.create(company=alpha, item_code="A-I", item_name="A item")


@pytest.fixture
def b_item(beta):
    return Item.objects.create(company=beta, item_code="B-I", item_name="B item")


@pytest.fixture
def b_customer(beta):
    return Customer.objects.create(company=beta, name="Beta customer")


@pytest.fixture
def a_customer(alpha):
    return Customer.objects.create(company=alpha, name="Alpha customer")


@pytest.mark.django_db
class TestReadScopingStillHolds:
    def test_attacker_cannot_see_the_other_company(self, client, b_customer):
        r = client.get("/api/selling/customers/")
        count = r.data.get("count", len(r.data.get("results", [])))
        assert count == 0


@pytest.mark.django_db
class TestCrossCompanyWritesBlocked:
    def test_sales_order_with_foreign_customer(
        self, client, alpha, a_branch, a_warehouse, b_customer
    ):
        r = client.post("/api/selling/sales-orders/", {
            "company": alpha.pk, "customer": b_customer.pk, "so_number": "X-1",
            "transaction_date": "2026-01-10", "branch": a_branch.pk,
            "warehouse": a_warehouse.pk,
        }, format="json")
        assert r.status_code == 400
        assert "customer" in r.data

    def test_sales_order_line_with_foreign_item(
        self, client, alpha, a_branch, a_warehouse, a_customer, b_item
    ):
        r = client.post("/api/selling/sales-orders/", {
            "company": alpha.pk, "customer": a_customer.pk, "so_number": "X-2",
            "transaction_date": "2026-01-10", "branch": a_branch.pk,
            "warehouse": a_warehouse.pk,
            "items": [{"item": b_item.pk, "qty": "1", "rate": "10"}],
        }, format="json")
        assert r.status_code == 400

    def test_sales_order_with_foreign_branch(
        self, client, alpha, a_customer, b_branch
    ):
        r = client.post("/api/selling/sales-orders/", {
            "company": alpha.pk, "customer": a_customer.pk, "so_number": "X-3",
            "transaction_date": "2026-01-10", "branch": b_branch.pk,
        }, format="json")
        assert r.status_code == 400
        assert "branch" in r.data

    def test_purchase_order_with_foreign_supplier(self, client, alpha, beta, a_branch):
        b_supplier = Supplier.objects.create(company=beta, name="Beta supplier")
        r = client.post("/api/buying/purchase-orders/", {
            "company": alpha.pk, "supplier": b_supplier.pk, "po_number": "X-4",
            "transaction_date": "2026-01-10", "branch": a_branch.pk,
        }, format="json")
        assert r.status_code == 400
        assert "supplier" in r.data

    def test_stock_entry_with_foreign_item(self, client, alpha, a_warehouse, b_item):
        r = client.post("/api/inventory/stock-entries/", {
            "company": alpha.pk, "warehouse": a_warehouse.pk, "item": b_item.pk,
            "entry_type": "Receipt", "quantity": "1", "rate": "1",
        }, format="json")
        assert r.status_code == 400

    def test_stock_entry_into_a_foreign_warehouse(self, client, alpha, b_branch, a_item):
        b_wh = Warehouse.objects.get(branch=b_branch)
        r = client.post("/api/inventory/stock-entries/", {
            "company": alpha.pk, "warehouse": b_wh.pk, "item": a_item.pk,
            "entry_type": "Receipt", "quantity": "1", "rate": "1",
        }, format="json")
        assert r.status_code == 400

    def test_invoice_with_foreign_cost_center(self, client, alpha, beta):
        b_cc = CostCenter.objects.create(company=beta, name="Beta CC")
        r = client.post("/api/invoicing/invoices/", {
            "company": alpha.pk, "invoice_type": "sales", "invoice_number": "X-5",
            "party_name": "Acme", "invoice_date": "2026-01-10", "cost_center": b_cc.pk,
        }, format="json")
        assert r.status_code == 400

    def test_invoice_line_with_foreign_item(self, client, alpha, b_item):
        r = client.post("/api/invoicing/invoices/", {
            "company": alpha.pk, "invoice_type": "sales", "invoice_number": "X-6",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [{"item": b_item.pk, "qty": "1", "rate": "10"}],
        }, format="json")
        assert r.status_code == 400

    def test_employee_in_a_foreign_department(self, client, alpha, beta):
        b_dept = Department.objects.create(company=beta, name="Beta dept")
        r = client.post("/api/hr/employees/", {
            "company": alpha.pk, "department": b_dept.pk, "employee_id": "X-7",
            "first_name": "A", "last_name": "B", "date_of_joining": "2025-01-01",
        }, format="json")
        assert r.status_code == 400

    def test_bom_with_foreign_item(self, client, alpha, b_item):
        r = client.post("/api/manufacturing/boms/", {
            "company": alpha.pk, "item": b_item.pk, "bom_name": "X-8", "quantity": 1,
        }, format="json")
        assert r.status_code == 400

    def test_journal_entry_with_foreign_account(self, client, alpha, beta):
        a_acc = Account.objects.create(
            company=alpha, account_number="1000", account_name="Cash", account_type="Asset"
        )
        b_acc = Account.objects.create(
            company=beta, account_number="4000", account_name="Rev", account_type="Income"
        )
        r = client.post("/api/accounts/journal-entries/", {
            "company": alpha.pk, "entry_number": "X-9", "posting_date": "2026-01-10",
            "debit_account": a_acc.pk, "credit_account": b_acc.pk, "amount": "100",
            "total_debit": "100", "total_credit": "100",
        }, format="json")
        assert r.status_code == 400


@pytest.mark.django_db
class TestLegitimateWritesStillWork:
    """The guard must not break the normal path."""

    def test_own_company_sales_order_succeeds(
        self, client, alpha, a_branch, a_warehouse, a_customer, a_item
    ):
        r = client.post("/api/selling/sales-orders/", {
            "company": alpha.pk, "customer": a_customer.pk, "so_number": "OK-1",
            "transaction_date": "2026-01-10", "branch": a_branch.pk,
            "warehouse": a_warehouse.pk,
            "items": [{"item": a_item.pk, "qty": "2", "rate": "50"}],
        }, format="json")
        assert r.status_code == 201, r.data
        assert len(r.data["items"]) == 1

    def test_own_company_invoice_with_lines_succeeds(self, client, alpha, a_item):
        r = client.post("/api/invoicing/invoices/", {
            "company": alpha.pk, "invoice_type": "sales", "invoice_number": "OK-2",
            "party_name": "Acme", "invoice_date": "2026-01-10",
            "line_items": [{"item": a_item.pk, "qty": "1", "rate": "100"}],
        }, format="json")
        assert r.status_code == 201, r.data

    def test_nullable_references_are_not_flagged(self, client, alpha, a_customer):
        r = client.post("/api/selling/sales-orders/", {
            "company": alpha.pk, "customer": a_customer.pk, "so_number": "OK-3",
            "transaction_date": "2026-01-10",
        }, format="json")
        assert r.status_code == 201, r.data
