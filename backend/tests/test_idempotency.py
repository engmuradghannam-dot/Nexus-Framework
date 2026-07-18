"""Side-effect operations must be idempotent.

Every posting operation was safe only because the status transition happened to
call it once. Called again — directly, from a management command, or a retried
request — each one repeated its effect: journal entries doubled balances,
deliveries issued stock twice, production ran twice, reconciliations posted
their adjustments twice. The guard has to live in the operation, not in the one
caller that happens to be careful.
"""
from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.models import Account, JournalEntry
from apps.buying.models import (
    GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem, Supplier,
)
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import (
    Item, StockEntry, StockReconciliation, StockReconciliationItem,
)
from apps.manufacturing.models import BOM, BOMItem, WorkOrder
from apps.selling.models import Customer, SalesOrder, SalesOrderItem


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Idem Co", code="IDEM-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="IDM-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="I-1", item_name="Thing")


def stock(company, warehouse, item, qty):
    return StockEntry.objects.create(
        company=company, warehouse=warehouse, item=item,
        entry_type="Receipt", quantity=qty, rate=1,
    )


@pytest.mark.django_db
class TestJournalPostingIdempotent:
    def _entry(self, company):
        dr = Account.objects.create(company=company, account_number="1000", account_name="Cash", account_type="Asset")
        cr = Account.objects.create(company=company, account_number="4000", account_name="Rev", account_type="Income")
        return JournalEntry.objects.create(
            company=company, entry_number="J-1", posting_date=date.today(),
            debit_account=dr, credit_account=cr, amount=Decimal("500"),
            total_debit=Decimal("500"), total_credit=Decimal("500"), status="Draft",
        ), dr

    def test_posting_twice_does_not_double_the_balance(self, company):
        je, dr = self._entry(company)
        je.post_to_ledger()
        dr.refresh_from_db()
        first = dr.balance
        je.post_to_ledger()
        dr.refresh_from_db()
        assert dr.balance == first

    def test_posted_flag_is_set(self, company):
        je, _ = self._entry(company)
        assert je.posted is False
        je.post_to_ledger()
        je.refresh_from_db()
        assert je.posted is True


@pytest.mark.django_db
class TestDeliveryIdempotent:
    def _order(self, company, branch, warehouse, item):
        stock(company, warehouse, item, 100)
        so = SalesOrder.objects.create(
            company=company, customer=Customer.objects.create(company=company, name="c"),
            so_number="S-1", transaction_date=date.today(), branch=branch,
            warehouse=warehouse, status="Draft",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=30, rate=10)
        so.recalculate_totals()
        so.status = "Submitted"
        so.save()
        so.reserve_stock()
        return so

    def test_delivering_twice_does_not_issue_stock_twice(
        self, company, branch, warehouse, item
    ):
        so = self._order(company, branch, warehouse, item)
        so.deliver_stock()
        after_first = item.stock_in_warehouse(warehouse)
        so.deliver_stock()
        assert item.stock_in_warehouse(warehouse) == after_first
        assert after_first == Decimal("70.00")


@pytest.mark.django_db
class TestProductionIdempotent:
    def test_completing_twice_does_not_produce_twice(self, company, branch, warehouse):
        rm = Item.objects.create(company=company, item_code="RM", item_name="rm")
        fg = Item.objects.create(company=company, item_code="FG", item_name="fg")
        stock(company, warehouse, rm, 1000)
        bom = BOM.objects.create(company=company, item=fg, bom_name="b", quantity=1)
        BOMItem.objects.create(bom=bom, item=rm, qty=2, rate=1)
        wo = WorkOrder.objects.create(
            company=company, branch=branch, warehouse=warehouse, bom=bom,
            wo_number="W-1", order_date=date.today(), item_to_manufacture=fg,
            qty_to_produce=10, status="Draft",
        )
        wo.release(ignore_bom_approval=True)
        wo.complete_production()
        first = fg.stock_in_warehouse(warehouse)
        wo.complete_production()
        assert fg.stock_in_warehouse(warehouse) == first
        assert first == Decimal("10.00")


@pytest.mark.django_db
class TestReconciliationIdempotent:
    def test_applying_twice_does_not_adjust_twice(self, company, branch, warehouse, item):
        stock(company, warehouse, item, 50)
        rec = StockReconciliation.objects.create(
            company=company, branch=branch, warehouse=warehouse,
            reconciliation_date=date.today(),
        )
        StockReconciliationItem.objects.create(
            reconciliation=rec, item=item, system_quantity=50, actual_quantity=60
        )
        rec.apply_adjustments()
        first = item.stock_in_warehouse(warehouse)
        rec.apply_adjustments()
        assert item.stock_in_warehouse(warehouse) == first
        assert first == Decimal("60.00")


@pytest.mark.django_db
class TestGoodsReceiptStillGuarded:
    """This one already guarded itself; the test pins the behaviour so a
    refactor can't quietly remove it."""

    def test_submitting_twice_does_not_receive_twice(self, company, branch, warehouse, item):
        from django.core.exceptions import ValidationError

        po = PurchaseOrder.objects.create(
            company=company, supplier=Supplier.objects.create(company=company, name="s"),
            po_number="P-1", transaction_date=date.today(), branch=branch,
            warehouse=warehouse, status="Submitted",
        )
        PurchaseOrderItem.objects.create(purchase_order=po, item=item, qty=100, rate=5)
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="G-1",
            receipt_date=date.today(), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=100
        )
        grn.submit()
        first = item.stock_in_warehouse(warehouse)
        with pytest.raises(ValidationError):
            grn.submit()
        assert item.stock_in_warehouse(warehouse) == first
