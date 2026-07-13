"""Pytest tests for the Manufacturing module (apps.manufacturing): BOM
costing and the work order production cycle (MRP-style raw material
consumption). Previously untested (P1 #4 follow-up).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.manufacturing.models import BOM, BOMItem, WorkOrder


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="production@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Manufacturing Co", code="MFG-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Plant", code="PLANT", address="Dammam")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.create(branch=branch, name="Plant WH", code="PWH")


@pytest.fixture
def finished_good(company):
    return Item.objects.create(company=company, item_code="FG-1", item_name="Chair", standard_rate=150)


@pytest.fixture
def raw_material(company):
    return Item.objects.create(company=company, item_code="RM-1", item_name="Wood Plank", standard_rate=10)


@pytest.fixture
def screws(company):
    return Item.objects.create(company=company, item_code="RM-2", item_name="Screws", standard_rate=1)


@pytest.fixture
def bom(company, finished_good, raw_material, screws):
    b = BOM.objects.create(
        company=company, item=finished_good, bom_name="Chair BOM",
        operating_cost=20, labor_cost=30,
    )
    BOMItem.objects.create(bom=b, item=raw_material, qty=4, rate=10)
    BOMItem.objects.create(bom=b, item=screws, qty=8, rate=1)
    return b


@pytest.fixture
def work_order(company, branch, warehouse, bom, finished_good):
    return WorkOrder.objects.create(
        company=company, branch=branch, bom=bom, wo_number="WO-001",
        item_to_manufacture=finished_good, qty_to_produce=5, warehouse=warehouse,
    )


@pytest.mark.django_db
class TestBOMCosting:
    def test_raw_materials_cost_sums_line_items(self, bom):
        # 4 * 10 (wood) + 8 * 1 (screws) = 48
        assert bom.raw_materials_cost == Decimal("48")

    def test_total_cost_adds_operating_and_labor(self, bom):
        # 48 raw materials + 20 operating + 30 labor = 98
        assert bom.total_cost == Decimal("98")


@pytest.mark.django_db
class TestCompleteProduction:
    def test_completing_with_sufficient_materials_issues_and_receipts(
        self, company, branch, warehouse, work_order, raw_material, screws, finished_good
    ):
        # Need 5 units produced: 5*4=20 wood, 5*8=40 screws.
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=raw_material,
            entry_type="Receipt", quantity=20, rate=10,
        )
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=screws,
            entry_type="Receipt", quantity=40, rate=1,
        )
        work_order.actual_cost = 500
        work_order.save()
        work_order.complete_production()

        assert raw_material.stock_quantity == 0
        assert screws.stock_quantity == 0
        assert finished_good.stock_quantity == 5

        receipt = StockEntry.objects.get(item=finished_good, entry_type="Receipt")
        assert receipt.quantity == 5
        assert receipt.rate == 100  # actual_cost / qty_to_produce = 500 / 5

        work_order.refresh_from_db()
        assert work_order.produced_qty == 5

    def test_completing_with_insufficient_materials_raises_and_consumes_nothing(
        self, company, branch, warehouse, work_order, raw_material, screws
    ):
        # Only enough wood, screws are short.
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=raw_material,
            entry_type="Receipt", quantity=20, rate=10,
        )
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=screws,
            entry_type="Receipt", quantity=10, rate=1,  # need 40, only have 10
        )
        with pytest.raises(ValidationError):
            work_order.complete_production()
        # All-or-nothing: the wood that WAS sufficient must not be consumed either.
        assert raw_material.stock_quantity == 20
        assert not StockEntry.objects.filter(item=raw_material, entry_type="Issue").exists()

    def test_completing_without_bom_raises(self, company, branch, warehouse, finished_good):
        wo = WorkOrder.objects.create(
            company=company, branch=branch, wo_number="WO-NOBOM",
            item_to_manufacture=finished_good, qty_to_produce=1, warehouse=warehouse,
        )
        with pytest.raises(ValidationError):
            wo.complete_production()

    def test_completing_without_warehouse_raises(self, company, bom, finished_good):
        wo = WorkOrder.objects.create(
            company=company, bom=bom, wo_number="WO-NOWH",
            item_to_manufacture=finished_good, qty_to_produce=1,
        )
        with pytest.raises(ValidationError):
            wo.complete_production()


@pytest.mark.django_db
class TestWorkOrderAPI:
    def test_start_then_complete_via_status_transition(
        self, auth_client, work_order, company, branch, warehouse, raw_material, screws
    ):
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=raw_material,
            entry_type="Receipt", quantity=20, rate=10,
        )
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=screws,
            entry_type="Receipt", quantity=40, rate=1,
        )
        r1 = auth_client.patch(f"/api/manufacturing/work-orders/{work_order.id}/", {"status": "In Progress"})
        assert r1.status_code == status.HTTP_200_OK

        r2 = auth_client.patch(f"/api/manufacturing/work-orders/{work_order.id}/", {"status": "Completed"})
        assert r2.status_code == status.HTTP_200_OK

    def test_invalid_status_transition_rejected(self, auth_client, work_order):
        response = auth_client.patch(
            f"/api/manufacturing/work-orders/{work_order.id}/", {"status": "Completed"}
        )
        # Draft -> Completed directly is not an allowed transition.
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/manufacturing/work-orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
