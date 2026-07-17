"""Tests for PRC-CTRL-002 (budget compliance), WHS-CTRL-003 (cycle count) and
WHS-RULE-003 (cross-docking) from ERP_Complete_System.xlsx.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Account, Budget, CostCenter
from apps.buying.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from apps.core.models import BinLocation, Branch, CompanyProfile, CycleCount, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.selling.models import Customer, SalesOrder, SalesOrderItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="bcc@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="BCC Co", code="BCC-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="BCC-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def supplier(company):
    return Supplier.objects.create(company=company, name="Vendor")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="B-1", item_name="Thing", standard_rate=10)


@pytest.fixture
def cost_center(company):
    return CostCenter.objects.create(company=company, name="Ops")


@pytest.fixture
def expense_account(company):
    return Account.objects.create(
        company=company, account_number="5100", account_name="Supplies",
        account_type="Expense",
    )


def make_po(company, supplier, branch, warehouse, item, qty, rate, number, cc=None):
    po = PurchaseOrder.objects.create(
        company=company, supplier=supplier, branch=branch, warehouse=warehouse,
        po_number=number, transaction_date=date(2026, 6, 15), status="Draft",
        cost_center=cc,
    )
    PurchaseOrderItem.objects.create(purchase_order=po, item=item, qty=qty, rate=rate)
    po.recalculate_totals()
    po.refresh_from_db()
    return po


@pytest.mark.django_db
class TestBudgetCompliance:
    """PRC-CTRL-002."""

    @pytest.fixture
    def budget(self, company, cost_center, expense_account):
        return Budget.objects.create(
            company=company, name="Ops 2026", fiscal_year="2026",
            cost_center=cost_center, account=expense_account,
            budget_amount=Decimal("10000"),
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )

    def test_po_within_budget_passes(self, company, supplier, branch, warehouse, item, cost_center, budget):
        po = make_po(company, supplier, branch, warehouse, item, 100, 10, "PO-B1", cost_center)
        po.check_budget()

    def test_po_over_budget_blocked(self, company, supplier, branch, warehouse, item, cost_center, budget):
        po = make_po(company, supplier, branch, warehouse, item, 2000, 10, "PO-B2", cost_center)
        with pytest.raises(ValidationError, match="Budget exceeded"):
            po.check_budget()

    def test_committed_pos_consume_the_budget(
        self, company, supplier, branch, warehouse, item, cost_center, budget
    ):
        """actual_amount is never written by anything, so a check that only read
        it would pass every PO no matter what was already committed."""
        first = make_po(company, supplier, branch, warehouse, item, 900, 10, "PO-B3", cost_center)
        first.status = "Submitted"
        first.save()
        assert budget.committed_amount == Decimal("9000.00")
        second = make_po(company, supplier, branch, warehouse, item, 200, 10, "PO-B4", cost_center)
        with pytest.raises(ValidationError, match="Budget exceeded"):
            second.check_budget()

    def test_po_without_a_cost_center_is_unbudgeted(
        self, company, supplier, branch, warehouse, item, budget
    ):
        po = make_po(company, supplier, branch, warehouse, item, 5000, 10, "PO-B5")
        po.check_budget()

    def test_cost_center_without_a_budget_passes(
        self, company, supplier, branch, warehouse, item, cost_center
    ):
        po = make_po(company, supplier, branch, warehouse, item, 5000, 10, "PO-B6", cost_center)
        po.check_budget()

    def test_budget_outside_the_po_date_does_not_apply(
        self, company, supplier, branch, warehouse, item, cost_center, expense_account
    ):
        Budget.objects.create(
            company=company, name="Ops 2025", fiscal_year="2025", cost_center=cost_center,
            account=expense_account, budget_amount=Decimal("1"),
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        po = make_po(company, supplier, branch, warehouse, item, 100, 10, "PO-B7", cost_center)
        po.check_budget()

    def test_available_amount_nets_actual_and_committed(
        self, company, supplier, branch, warehouse, item, cost_center, budget
    ):
        budget.actual_amount = Decimal("2000")
        budget.save()
        po = make_po(company, supplier, branch, warehouse, item, 300, 10, "PO-B8", cost_center)
        po.status = "Submitted"
        po.save()
        assert budget.available_amount == Decimal("5000.00")  # 10000 - 2000 - 3000


@pytest.mark.django_db
class TestCycleCount:
    """WHS-CTRL-003."""

    @pytest.fixture
    def zoned(self, company, warehouse):
        bin_a = BinLocation.objects.create(warehouse=warehouse, code="A-01", zone="A")
        items = []
        for n in range(4):
            it = Item.objects.create(company=company, item_code=f"Z-{n}", item_name=f"Z{n}")
            StockEntry.objects.create(
                company=company, warehouse=warehouse, bin_location=bin_a, item=it,
                entry_type="Receipt", quantity=10, rate=5,
            )
            items.append(it)
        return items

    def test_generate_samples_items_from_the_zone(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=2)
        assert c.lines.count() == 2
        assert all(l.item in zoned for l in c.lines.all())

    def test_sample_size_caps_at_what_exists(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=99)
        assert c.lines.count() == 4

    def test_system_qty_snapshotted_at_draw_time(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=1)
        assert c.lines.first().system_qty == Decimal("10.00")

    def test_empty_zone_rejected(self, warehouse):
        with pytest.raises(ValidationError, match="No stock recorded"):
            CycleCount.generate(warehouse, "EMPTY", date.today())

    def test_uncounted_line_has_no_variance(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=1)
        assert c.lines.first().counted_qty is None
        assert c.lines.first().variance == Decimal(0)
        assert c.has_discrepancy is False

    def test_variance_detected(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=1)
        line = c.lines.first()
        line.counted_qty = Decimal("7")
        line.save()
        assert line.variance == Decimal("-3.00")
        assert c.has_discrepancy is True

    def test_reconcile_posts_the_difference(self, company, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=1)
        line = c.lines.first()
        line.counted_qty = Decimal("7")
        line.save()
        c.status = "Counted"
        c.save()
        c.reconcile()
        c.refresh_from_db()
        assert c.status == "Reconciled"
        assert line.item.stock_in_warehouse(warehouse) == Decimal("7.00")

    def test_cannot_reconcile_before_counting(self, warehouse, zoned):
        c = CycleCount.generate(warehouse, "A", date.today(), sample_size=1)
        with pytest.raises(ValidationError, match="Only a counted"):
            c.reconcile()

    def test_api_generate_and_reconcile(self, auth_client, warehouse, zoned):
        response = auth_client.post("/api/core/cycle-counts/generate/", {
            "warehouse": warehouse.pk, "zone": "A", "sample_size": 2,
        }, format="json")
        assert response.status_code == 201
        assert len(response.data["lines"]) == 2


@pytest.mark.django_db
class TestCrossDocking:
    """WHS-RULE-003."""

    @pytest.fixture
    def po(self, company, supplier, branch, warehouse, item):
        po = make_po(company, supplier, branch, warehouse, item, 100, 10, "PO-XD")
        po.status = "Submitted"
        po.save()
        return po

    def grn(self, company, po, warehouse, qty, number="GRN-XD"):
        g = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number=number,
            receipt_date=date.today(), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=g, po_item=po.items.first(), qty_received=qty
        )
        return g

    def demand(self, company, warehouse, branch, item, qty, number):
        c = Customer.objects.create(company=company, name=f"C-{number}")
        so = SalesOrder.objects.create(
            company=company, customer=c, so_number=number, transaction_date=date.today(),
            branch=branch, warehouse=warehouse, status="Submitted",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=qty, rate=20)
        return so

    def test_inbound_matched_to_an_open_order(self, company, po, warehouse, branch, item):
        so = self.demand(company, warehouse, branch, item, 30, "SO-XD1")
        g = self.grn(company, po, warehouse, 50)
        matches = g.cross_dock_candidates()
        assert len(matches) == 1
        assert matches[0][1] == so and matches[0][2] == Decimal("30.00")

    def test_no_demand_means_no_cross_dock(self, company, po, warehouse):
        g = self.grn(company, po, warehouse, 50)
        assert g.cross_dock_candidates() == []

    def test_oldest_order_is_filled_first(self, company, po, warehouse, branch, item):
        old = self.demand(company, warehouse, branch, item, 30, "SO-OLD")
        old.transaction_date = date(2026, 1, 1)
        old.save()
        new = self.demand(company, warehouse, branch, item, 30, "SO-NEW")
        g = self.grn(company, po, warehouse, 40)
        matches = g.cross_dock_candidates()
        assert matches[0][1] == old and matches[0][2] == Decimal("30.00")
        assert matches[1][1] == new and matches[1][2] == Decimal("10.00")

    def test_rejected_qty_is_not_cross_docked(self, company, po, warehouse, branch, item):
        self.demand(company, warehouse, branch, item, 50, "SO-XD2")
        g = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-REJ",
            receipt_date=date.today(), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=g, po_item=po.items.first(), qty_received=50, qty_rejected=20
        )
        assert g.cross_dock_candidates()[0][2] == Decimal("30.00")

    def test_demand_at_another_warehouse_does_not_match(
        self, company, po, warehouse, branch, item
    ):
        other = Warehouse.objects.create(branch=branch, name="Other", code="XD-O")
        self.demand(company, other, branch, item, 30, "SO-XD3")
        g = self.grn(company, po, warehouse, 50)
        assert g.cross_dock_candidates() == []

    def test_api_lists_candidates(self, auth_client, company, po, warehouse, branch, item):
        self.demand(company, warehouse, branch, item, 30, "SO-XD4")
        g = self.grn(company, po, warehouse, 50)
        response = auth_client.get(f"/api/buying/goods-receipts/{g.pk}/cross_dock/")
        assert response.status_code == 200
        assert response.data["candidates"][0]["qty"] == "30.00"
