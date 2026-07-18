"""Deleting a master that financial history points at must be refused.

Every FK from a ledger record to its master was on_delete=CASCADE, so deleting
one item erased all its stock movements; deleting one account erased its journal
lines and unbalanced the entries referencing them. Verified before the fix by
deleting the master and watching the ledger rows vanish. These are financial
records — the delete must be blocked, not silently cascade.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.db.models import ProtectedError
from rest_framework.test import APIClient

from apps.accounts.models import Account, JournalEntry, JournalEntryLine
from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.selling.models import Customer, SalesOrder, SalesOrderItem


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Prot Co", code="PROT-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="PRT-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="P-1", item_name="Thing")


@pytest.fixture
def auth_client(db, django_user_model, company):
    u = django_user_model.objects.create_superuser(email="prot@x.com", password="x")
    company.super_admin = u
    company.save(update_fields=["super_admin"])
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.mark.django_db
class TestDeleteIsRefusedAtTheModel:
    def test_item_with_stock_movements(self, company, warehouse, item):
        StockEntry.objects.create(
            company=company, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=10, rate=1,
        )
        with pytest.raises(ProtectedError):
            item.delete()
        assert Item.objects.filter(pk=item.pk).exists()

    def test_warehouse_with_stock_movements(self, company, branch, warehouse, item):
        StockEntry.objects.create(
            company=company, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=10, rate=1,
        )
        with pytest.raises(ProtectedError):
            warehouse.delete()

    def test_customer_with_sales_orders(self, company, branch, warehouse):
        cust = Customer.objects.create(company=company, name="c")
        SalesOrder.objects.create(
            company=company, customer=cust, so_number="S-1",
            transaction_date=date.today(), branch=branch, warehouse=warehouse,
        )
        with pytest.raises(ProtectedError):
            cust.delete()

    def test_supplier_with_purchase_orders(self, company, branch, warehouse):
        sup = Supplier.objects.create(company=company, name="s")
        PurchaseOrder.objects.create(
            company=company, supplier=sup, po_number="P-1",
            transaction_date=date.today(), branch=branch, warehouse=warehouse,
        )
        with pytest.raises(ProtectedError):
            sup.delete()

    def test_account_with_journal_lines(self, company):
        acc = Account.objects.create(
            company=company, account_number="1000", account_name="Cash", account_type="Asset"
        )
        je = JournalEntry.objects.create(
            company=company, entry_number="J-1", posting_date=date.today(),
            total_debit=100, total_credit=100,
        )
        JournalEntryLine.objects.create(journal_entry=je, account=acc, debit=100, credit=0)
        with pytest.raises(ProtectedError):
            acc.delete()

    def test_item_on_a_sales_order_line(self, company, branch, warehouse, item):
        so = SalesOrder.objects.create(
            company=company, customer=Customer.objects.create(company=company, name="c"),
            so_number="S-2", transaction_date=date.today(), branch=branch, warehouse=warehouse,
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=1, rate=10)
        with pytest.raises(ProtectedError):
            item.delete()


@pytest.mark.django_db
class TestDeleteReturnsCleanApiError:
    def test_api_delete_returns_409_not_500(self, auth_client, company, warehouse, item):
        StockEntry.objects.create(
            company=company, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=10, rate=1,
        )
        r = auth_client.delete(f"/api/inventory/items/{item.pk}/")
        assert r.status_code == 409
        assert "cannot be deleted" in r.data["detail"]


@pytest.mark.django_db
class TestUnreferencedMastersStillDelete:
    """PROTECT must only bite when history actually points at the record."""

    def test_item_with_no_movements_deletes(self, item):
        pk = item.pk
        item.delete()
        assert not Item.objects.filter(pk=pk).exists()

    def test_customer_with_no_orders_deletes(self, company):
        cust = Customer.objects.create(company=company, name="unused")
        pk = cust.pk
        cust.delete()
        assert not Customer.objects.filter(pk=pk).exists()

    def test_account_with_no_lines_deletes(self, company):
        acc = Account.objects.create(
            company=company, account_number="9999", account_name="Unused", account_type="Asset"
        )
        pk = acc.pk
        acc.delete()
        assert not Account.objects.filter(pk=pk).exists()
