"""Tests for the warehouse location layer from ERP_Complete_System.xlsx.

Covers WHS-CTRL-001 (every item has a bin), WHS-RULE-001 (putaway logic) and
WHS-RULE-002 (pick sequence / wave picking).
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import BinLocation, Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, ItemGroup, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="bins@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Bin Co", code="BIN-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="BIN-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def group(company):
    return ItemGroup.objects.create(company=company, name="Chilled")


@pytest.fixture
def item(company, group):
    return Item.objects.create(
        company=company, item_code="B-1", item_name="Tray", item_group=group
    )


@pytest.mark.django_db
class TestBinRequirement:
    """WHS-CTRL-001 — but only for warehouses that actually use bins."""

    def test_unbinned_warehouse_still_accepts_stock(self, auth_client, company, warehouse, item):
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "5", "rate": "10",
        }, format="json")
        assert response.status_code == 201

    def test_binned_warehouse_requires_a_bin(self, auth_client, company, warehouse, item):
        BinLocation.objects.create(warehouse=warehouse, code="A-01", zone="A")
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "5", "rate": "10",
        }, format="json")
        assert response.status_code == 400
        assert "bin" in str(response.data).lower()

    def test_bin_from_another_warehouse_rejected(self, auth_client, company, warehouse, branch, item):
        other = Warehouse.objects.create(branch=branch, name="Other", code="OTH-B")
        foreign = BinLocation.objects.create(warehouse=other, code="X-01")
        BinLocation.objects.create(warehouse=warehouse, code="A-01")
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "bin_location": foreign.pk, "entry_type": "Receipt", "quantity": "5", "rate": "10",
        }, format="json")
        assert response.status_code == 400

    def test_bin_over_capacity_rejected(self, auth_client, company, warehouse, item):
        b = BinLocation.objects.create(warehouse=warehouse, code="A-01", capacity=10)
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "bin_location": b.pk, "entry_type": "Receipt", "quantity": "11", "rate": "10",
        }, format="json")
        assert response.status_code == 400

    def test_bin_code_unique_per_warehouse_only(self, warehouse, branch):
        other = Warehouse.objects.create(branch=branch, name="Other", code="OTH-C")
        BinLocation.objects.create(warehouse=warehouse, code="A-01")
        BinLocation.objects.create(warehouse=other, code="A-01")  # must not clash


@pytest.mark.django_db
class TestPutawayLogic:
    """WHS-RULE-001."""

    def test_prefers_a_bin_dedicated_to_the_item_group(self, warehouse, item, group):
        general = BinLocation.objects.create(warehouse=warehouse, code="G-01", pick_sequence=1)
        dedicated = BinLocation.objects.create(
            warehouse=warehouse, code="C-01", item_group=group, pick_sequence=9
        )
        assert warehouse.suggest_putaway_bin(item, 5) == dedicated

    def test_falls_back_to_a_general_bin(self, warehouse, item):
        general = BinLocation.objects.create(warehouse=warehouse, code="G-01")
        assert warehouse.suggest_putaway_bin(item, 5) == general

    def test_skips_a_dedicated_bin_that_is_full(self, company, warehouse, item, group):
        full = BinLocation.objects.create(
            warehouse=warehouse, code="C-01", item_group=group, capacity=5, pick_sequence=1
        )
        StockEntry.objects.create(
            company=company, warehouse=warehouse, bin_location=full, item=item,
            entry_type="Receipt", quantity=5, rate=1,
        )
        general = BinLocation.objects.create(warehouse=warehouse, code="G-01", pick_sequence=2)
        assert warehouse.suggest_putaway_bin(item, 3) == general

    def test_fast_route_position_wins_among_equals(self, warehouse, item, group):
        far = BinLocation.objects.create(
            warehouse=warehouse, code="C-09", item_group=group, pick_sequence=9
        )
        near = BinLocation.objects.create(
            warehouse=warehouse, code="C-01", item_group=group, pick_sequence=1
        )
        assert warehouse.suggest_putaway_bin(item, 1) == near

    def test_returns_none_when_nothing_fits(self, company, warehouse, item):
        b = BinLocation.objects.create(warehouse=warehouse, code="G-01", capacity=2)
        assert warehouse.suggest_putaway_bin(item, 50) is None

    def test_returns_none_for_a_warehouse_with_no_bins(self, warehouse, item):
        assert warehouse.suggest_putaway_bin(item, 1) is None

    def test_api_action(self, auth_client, warehouse, item, group):
        BinLocation.objects.create(warehouse=warehouse, code="C-01", item_group=group)
        response = auth_client.post(
            f"/api/core/warehouses/{warehouse.pk}/suggest_putaway/",
            {"item": item.pk, "qty": 3}, format="json",
        )
        assert response.status_code == 200
        assert response.data["bin"]["code"] == "C-01"


@pytest.mark.django_db
class TestPickRoute:
    """WHS-RULE-002: one walk through the warehouse, not a criss-cross."""

    def test_lines_ordered_by_pick_sequence(self, company, warehouse, group):
        far = BinLocation.objects.create(warehouse=warehouse, code="Z-99", pick_sequence=99)
        near = BinLocation.objects.create(warehouse=warehouse, code="A-01", pick_sequence=1)
        a = Item.objects.create(company=company, item_code="FAR", item_name="Far")
        b = Item.objects.create(company=company, item_code="NEAR", item_name="Near")
        for it, bin_ in [(a, far), (b, near)]:
            StockEntry.objects.create(
                company=company, warehouse=warehouse, bin_location=bin_, item=it,
                entry_type="Receipt", quantity=10, rate=1,
            )
        route = warehouse.pick_route([(a, 1), (b, 1)])
        assert [r[1].item_code for r in route] == ["NEAR", "FAR"]

    def test_items_without_stock_are_reported_not_dropped(self, company, warehouse):
        ghost = Item.objects.create(company=company, item_code="GHOST", item_name="Ghost")
        route = warehouse.pick_route([(ghost, 3)])
        assert len(route) == 1
        assert route[0][0] is None and route[0][1] == ghost

    def test_unstocked_lines_sort_last(self, company, warehouse):
        b = BinLocation.objects.create(warehouse=warehouse, code="A-01", pick_sequence=5)
        real = Item.objects.create(company=company, item_code="REAL", item_name="Real")
        ghost = Item.objects.create(company=company, item_code="GHOST", item_name="Ghost")
        StockEntry.objects.create(
            company=company, warehouse=warehouse, bin_location=b, item=real,
            entry_type="Receipt", quantity=5, rate=1,
        )
        route = warehouse.pick_route([(ghost, 1), (real, 1)])
        assert [r[1].item_code for r in route] == ["REAL", "GHOST"]

    def test_api_action(self, auth_client, company, warehouse):
        b = BinLocation.objects.create(warehouse=warehouse, code="A-01", zone="A", pick_sequence=1)
        it = Item.objects.create(company=company, item_code="R-1", item_name="R")
        StockEntry.objects.create(
            company=company, warehouse=warehouse, bin_location=b, item=it,
            entry_type="Receipt", quantity=5, rate=1,
        )
        response = auth_client.post(
            f"/api/core/warehouses/{warehouse.pk}/pick_route/",
            {"lines": [{"item": it.pk, "qty": 2}]}, format="json",
        )
        assert response.status_code == 200
        assert response.data["route"][0]["bin"] == "A-01"
