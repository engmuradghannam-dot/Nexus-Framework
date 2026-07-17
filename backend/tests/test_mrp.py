"""Tests for the manufacturing/MRP rules from ERP_Complete_System.xlsx.

Covers MFG-RULE-001 (MRP from BOM), MFG-RULE-002 (material reservation),
MFG-RULE-003 (yield), MFG-RULE-005 (scrap cost allocation),
MFG-CTRL-001 (BOM approval), MFG-CTRL-003 (material availability) and
MFG-CTRL-004 (yield variance).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.hr.models import Department, Employee
from apps.inventory.models import Item, StockEntry
from apps.manufacturing.models import BOM, BOMItem, MaterialReservation, WorkOrder


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="mrp@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="MRP Co", code="MRP-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Plant", code="MRP-P", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def engineer(company):
    dept = Department.objects.create(company=company, name="Engineering")
    return Employee.objects.create(
        company=company, department=dept, employee_id="ENG-1",
        first_name="Eng", last_name="Manager", date_of_joining=date(2025, 1, 1),
    )


@pytest.fixture
def finished(company):
    return Item.objects.create(company=company, item_code="FG-1", item_name="Widget")


@pytest.fixture
def flour(company):
    return Item.objects.create(company=company, item_code="RM-1", item_name="Flour")


@pytest.fixture
def batch_bom(company, finished, flour):
    """A recipe that yields 10 units from 5 kg — the case the old code got wrong."""
    bom = BOM.objects.create(
        company=company, item=finished, bom_name="Batch BOM", quantity=10,
    )
    BOMItem.objects.create(bom=bom, item=flour, qty=5, rate=20)
    return bom


def stock(company, warehouse, item, qty, rate=20):
    return StockEntry.objects.create(
        company=company, warehouse=warehouse, item=item,
        entry_type="Receipt", quantity=qty, rate=rate,
    )


def make_wo(company, branch, warehouse, bom, finished, qty, number="WO-1"):
    return WorkOrder.objects.create(
        company=company, branch=branch, warehouse=warehouse, bom=bom,
        wo_number=number, order_date=date(2026, 1, 10),
        item_to_manufacture=finished, qty_to_produce=qty, status="Draft",
    )


@pytest.mark.django_db
class TestMRPExplosion:
    """MFG-RULE-001 — and the batch-size bug it fixes."""

    def test_requirements_scale_by_bom_batch_size(self, batch_bom):
        # 5 kg per 10 units -> 100 units needs 50 kg, not 500.
        reqs = batch_bom.requirements_for(100)
        assert [(l.item.item_code, q) for l, q in reqs] == [("RM-1", Decimal("50.00"))]

    def test_per_unit_bom_is_unchanged(self, company, finished, flour):
        bom = BOM.objects.create(company=company, item=finished, bom_name="Unit", quantity=1)
        BOMItem.objects.create(bom=bom, item=flour, qty=3, rate=10)
        assert bom.requirements_for(7)[0][1] == Decimal("21.00")

    def test_work_order_uses_the_scaled_requirement(
        self, company, branch, warehouse, batch_bom, finished
    ):
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        assert wo.material_requirements()[0][1] == Decimal("50.00")

    def test_cost_per_unit_spreads_the_batch(self, batch_bom):
        # 5 kg * 20 = 100 per batch of 10 -> 10 per unit
        assert batch_bom.cost_per_unit == Decimal("10.0000")

    def test_zero_batch_size_is_treated_as_one(self, company, finished, flour):
        bom = BOM.objects.create(company=company, item=finished, bom_name="Zero", quantity=0)
        BOMItem.objects.create(bom=bom, item=flour, qty=2, rate=1)
        assert bom.requirements_for(5)[0][1] == Decimal("10.00")


@pytest.mark.django_db
class TestBOMApproval:
    """MFG-CTRL-001."""

    def test_unapproved_bom_cannot_be_released(
        self, company, branch, warehouse, batch_bom, finished, flour
    ):
        stock(company, warehouse, flour, 100)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        with pytest.raises(ValidationError, match="not approved"):
            wo.release()

    def test_approved_bom_releases(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        stock(company, warehouse, flour, 100)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        ok, _ = wo.release()
        assert ok and wo.status == "In Progress"

    def test_approve_sets_who_and_when(self, batch_bom, engineer):
        assert batch_bom.is_approved is False
        batch_bom.approve(engineer)
        batch_bom.refresh_from_db()
        assert batch_bom.is_approved is True
        assert batch_bom.approved_by == engineer and batch_bom.approved_at is not None


@pytest.mark.django_db
class TestMaterialReservation:
    """MFG-RULE-002 + MFG-CTRL-003."""

    def test_release_reserves_the_exploded_quantity(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        stock(company, warehouse, flour, 100)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        wo.release()
        r = MaterialReservation.objects.get(work_order=wo)
        assert r.item == flour and r.qty == Decimal("50.00")

    def test_release_blocked_when_material_is_short(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        stock(company, warehouse, flour, 10)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        with pytest.raises(ValidationError, match="Insufficient raw materials"):
            wo.release()

    def test_a_second_order_cannot_claim_reserved_stock(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        """The bug this closes: both orders saw the same 50 kg as available."""
        stock(company, warehouse, flour, 60)
        batch_bom.approve(engineer)
        first = make_wo(company, branch, warehouse, batch_bom, finished, 100, "WO-A")
        first.release()
        second = make_wo(company, branch, warehouse, batch_bom, finished, 100, "WO-B")
        with pytest.raises(ValidationError, match="Insufficient raw materials"):
            second.release()

    def test_material_in_another_warehouse_does_not_count(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        other = Warehouse.objects.create(branch=branch, name="Other", code="MRP-O")
        stock(company, other, flour, 500)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        with pytest.raises(ValidationError, match="Insufficient raw materials"):
            wo.release()

    def test_re_release_replaces_rather_than_doubles(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        stock(company, warehouse, flour, 100)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        wo.release()
        wo.release()
        assert wo.reservations.count() == 1

    def test_completion_consumes_the_reservation(
        self, company, branch, warehouse, batch_bom, finished, flour, engineer
    ):
        stock(company, warehouse, flour, 100)
        batch_bom.approve(engineer)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        wo.release()
        wo.complete_production()
        assert wo.reservations.count() == 0
        assert flour.stock_in_warehouse(warehouse) == Decimal("50.00")


@pytest.mark.django_db
class TestYieldAndScrap:
    """MFG-RULE-003, MFG-RULE-005, MFG-CTRL-004."""

    @pytest.fixture
    def wo(self, company, branch, warehouse, batch_bom, finished, flour, engineer):
        stock(company, warehouse, flour, 100)
        batch_bom.approve(engineer)
        w = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        w.release()
        return w

    def test_scrap_reduces_the_finished_goods_received(self, wo, finished, warehouse):
        wo.scrap_qty = Decimal("10")
        wo.save()
        wo.complete_production()
        assert finished.stock_in_warehouse(warehouse) == Decimal("90.00")

    def test_yield_percent(self, wo):
        wo.scrap_qty = Decimal("10")
        wo.save()
        wo.complete_production()
        wo.refresh_from_db()
        assert wo.yield_percent == Decimal("90.00")

    def test_yield_variance_alert_over_5_percent(self, wo):
        wo.scrap_qty = Decimal("10")
        wo.save()
        wo.complete_production()
        wo.refresh_from_db()
        assert wo.yield_variance_exceeded is True

    def test_small_scrap_does_not_trigger_the_alert(self, wo):
        wo.scrap_qty = Decimal("3")
        wo.save()
        wo.complete_production()
        wo.refresh_from_db()
        assert wo.yield_percent == Decimal("97.00")
        assert wo.yield_variance_exceeded is False

    def test_scrap_cost_is_absorbed_by_the_good_units(self, wo, finished, warehouse):
        """MFG-RULE-005: the run cost doesn't shrink because units were lost —
        the survivors get more expensive."""
        wo.actual_cost = Decimal("1000")
        wo.scrap_qty = Decimal("20")
        wo.save()
        wo.complete_production()
        entry = StockEntry.objects.get(item=finished, entry_type="Receipt")
        assert entry.quantity == Decimal("80.00")
        assert entry.rate == Decimal("12.50")  # 1000 / 80, not 1000 / 100

    def test_scrap_cannot_exceed_the_plan(self, wo):
        wo.scrap_qty = Decimal("150")
        wo.save()
        with pytest.raises(ValidationError, match="cannot exceed the planned quantity"):
            wo.complete_production()


@pytest.mark.django_db
class TestMRPApi:
    def test_requirements_endpoint_reports_shortages(
        self, auth_client, company, branch, warehouse, batch_bom, finished, flour
    ):
        stock(company, warehouse, flour, 10)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        response = auth_client.get(f"/api/manufacturing/work-orders/{wo.pk}/material_requirements/")
        assert response.status_code == 200
        row = response.data["requirements"][0]
        assert row["required"] == "50.00" and row["short"] is True

    def test_release_endpoint_blocks_unapproved_bom(
        self, auth_client, company, branch, warehouse, batch_bom, finished, flour
    ):
        stock(company, warehouse, flour, 100)
        wo = make_wo(company, branch, warehouse, batch_bom, finished, 100)
        response = auth_client.post(f"/api/manufacturing/work-orders/{wo.pk}/release/")
        assert response.status_code == 400
        assert "not approved" in str(response.data)

    def test_bom_approve_endpoint(self, auth_client, batch_bom, engineer):
        response = auth_client.post(
            f"/api/manufacturing/boms/{batch_bom.pk}/approve/",
            {"employee": engineer.pk}, format="json",
        )
        assert response.status_code == 200
        batch_bom.refresh_from_db()
        assert batch_bom.is_approved is True
