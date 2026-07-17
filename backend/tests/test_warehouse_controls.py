"""Tests for the warehouse/inventory rules from ERP_Complete_System.xlsx.

Covers WHS-RULE-004 (zone capacity), WHS-CTRL-002 (90% alert),
WHS-RULE-005 (FEFO picking) and INV-RULE-003 (COGS by valuation method).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, ItemBatch, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="whs@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="WHS Co", code="WHS-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="WHS-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    wh = Warehouse.objects.get(branch=branch)
    wh.capacity = 100
    wh.save()
    return wh


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="W-1", item_name="Crate")


def receipt(company, warehouse, item, qty, rate=10, when=None):
    return StockEntry.objects.create(
        company=company, warehouse=warehouse, item=item,
        entry_type="Receipt", quantity=qty, rate=rate,
    )


@pytest.mark.django_db
class TestZoneCapacity:
    def test_whs_rule_004_receipt_within_capacity_allowed(self, warehouse):
        warehouse.check_capacity(50)

    def test_whs_rule_004_receipt_over_capacity_blocked(self, company, warehouse, item):
        receipt(company, warehouse, item, 80)
        with pytest.raises(ValidationError, match="Zone capacity exceeded"):
            warehouse.check_capacity(30)

    def test_whs_rule_004_unconfigured_capacity_is_not_enforced(self, branch):
        wh = Warehouse.objects.create(branch=branch, name="No Cap", code="NC", capacity=0)
        wh.check_capacity(999_999)  # must not raise

    def test_whs_rule_004_enforced_through_the_api(self, auth_client, company, warehouse, item):
        receipt(company, warehouse, item, 90)
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "20", "rate": "10",
        }, format="json")
        assert response.status_code == 400
        assert "capacity" in str(response.data).lower()

    def test_whs_ctrl_002_alert_at_90_percent(self, company, warehouse, item):
        receipt(company, warehouse, item, 89)
        assert warehouse.is_near_capacity is False
        receipt(company, warehouse, item, 1)
        assert warehouse.is_near_capacity is True

    def test_issues_free_up_capacity(self, company, warehouse, item):
        receipt(company, warehouse, item, 100)
        StockEntry.objects.create(
            company=company, warehouse=warehouse, item=item,
            entry_type="Issue", quantity=40, rate=10,
        )
        assert warehouse.occupancy_rate == 60.0


@pytest.mark.django_db
class TestFEFOPicking:
    """WHS-RULE-005: nearest expiry leaves first."""

    def _batch(self, item, warehouse, no, qty, days):
        return ItemBatch.objects.create(
            item=item, warehouse=warehouse, batch_no=no, quantity=qty,
            expiry_date=None if days is None else date.today() + timedelta(days=days),
        )

    def test_picks_nearest_expiry_first(self, item, warehouse):
        far = self._batch(item, warehouse, "B-FAR", 10, 90)
        near = self._batch(item, warehouse, "B-NEAR", 10, 5)
        plan = item.fefo_batches(warehouse, 6)
        assert plan == [(near, Decimal(6))]

    def test_spills_into_the_next_batch_in_expiry_order(self, item, warehouse):
        near = self._batch(item, warehouse, "B-NEAR", 4, 5)
        mid = self._batch(item, warehouse, "B-MID", 10, 30)
        far = self._batch(item, warehouse, "B-FAR", 10, 90)
        plan = item.fefo_batches(warehouse, 9)
        assert plan == [(near, Decimal(4)), (mid, Decimal(5))]

    def test_undated_batches_are_used_last(self, item, warehouse):
        undated = self._batch(item, warehouse, "B-NONE", 10, None)
        dated = self._batch(item, warehouse, "B-DATED", 4, 60)
        plan = item.fefo_batches(warehouse, 6)
        assert plan[0][0] == dated
        assert plan[1] == (undated, Decimal(2))

    def test_insufficient_batch_stock_raises(self, item, warehouse):
        self._batch(item, warehouse, "B-1", 3, 10)
        with pytest.raises(ValidationError, match="Insufficient batch stock"):
            item.fefo_batches(warehouse, 5)

    def test_batches_in_another_warehouse_are_not_picked(self, item, warehouse, branch):
        other = Warehouse.objects.create(branch=branch, name="Other", code="OTH")
        self._batch(item, other, "B-OTHER", 100, 10)
        with pytest.raises(ValidationError, match="Insufficient batch stock"):
            item.fefo_batches(warehouse, 1)


@pytest.mark.django_db
class TestCOGSValuation:
    """INV-RULE-003. The sheet says weighted average; Modules Overview says
    FIFO/FEFO. Item.valuation_method already existed, so it decides per item."""

    def test_fifo_uses_the_oldest_receipt_rate(self, company, warehouse, item):
        item.valuation_method = "FIFO"
        item.save()
        receipt(company, warehouse, item, 10, rate=100)
        receipt(company, warehouse, item, 10, rate=200)
        assert item.valuation_rate() == Decimal("100")
        assert item.cogs_for(5) == Decimal("500.00")

    def test_lifo_uses_the_newest_receipt_rate(self, company, warehouse, item):
        item.valuation_method = "LIFO"
        item.save()
        receipt(company, warehouse, item, 10, rate=100)
        receipt(company, warehouse, item, 10, rate=200)
        assert item.valuation_rate() == Decimal("200")

    def test_moving_average_weights_by_quantity(self, company, warehouse, item):
        item.valuation_method = "Moving Average"
        item.save()
        receipt(company, warehouse, item, 10, rate=100)
        receipt(company, warehouse, item, 30, rate=200)
        # (10*100 + 30*200) / 40 = 175
        assert item.valuation_rate() == Decimal("175.0000")
        assert item.cogs_for(4) == Decimal("700.00")

    def test_no_receipts_values_at_zero(self, item):
        assert item.valuation_rate() == Decimal(0)
        assert item.cogs_for(10) == Decimal("0.00")

    def test_valuation_can_be_scoped_to_one_warehouse(self, company, warehouse, branch, item):
        other = Warehouse.objects.create(branch=branch, name="Other", code="OTH2")
        item.valuation_method = "FIFO"
        item.save()
        receipt(company, other, item, 10, rate=999)
        receipt(company, warehouse, item, 10, rate=100)
        assert item.valuation_rate(warehouse) == Decimal("100")
