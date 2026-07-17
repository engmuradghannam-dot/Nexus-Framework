"""Tests for SAL-RULE-002 (stock reservation) and SAL-RULE-004 (backorders)
from ERP_Complete_System.xlsx.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.manufacturing.models import BOM, BOMItem, WorkOrder
from apps.selling.models import Customer, SalesOrder, SalesOrderItem, StockReservation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="res@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Res Co", code="RES-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="RES-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="R-1", item_name="Thing")


@pytest.fixture
def customer(company):
    return Customer.objects.create(company=company, name="Client")


def stock(company, warehouse, item, qty):
    return StockEntry.objects.create(
        company=company, warehouse=warehouse, item=item,
        entry_type="Receipt", quantity=qty, rate=10,
    )


def order(company, customer, branch, warehouse, item, qty, number="SO-R1"):
    so = SalesOrder.objects.create(
        company=company, customer=customer, so_number=number,
        transaction_date=date.today(), branch=branch, warehouse=warehouse, status="Draft",
    )
    SalesOrderItem.objects.create(sales_order=so, item=item, qty=qty, rate=10)
    so.recalculate_totals()
    so.refresh_from_db()
    return so


@pytest.mark.django_db
class TestStockReservation:
    """SAL-RULE-002."""

    def test_confirmation_reserves_available_stock(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        reserved, backorder = so.reserve_stock()
        assert reserved == 1 and backorder is None
        assert StockReservation.objects.get(sales_order=so).qty == Decimal("10.00")

    def test_reserved_stock_is_not_available_to_another_order(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 10)
        first = order(company, customer, branch, warehouse, item, 10, "SO-A")
        first.reserve_stock()
        first.status = "Submitted"
        first.save()
        assert item.available_qty(warehouse) == Decimal("0.00")

    def test_reservation_does_not_change_physical_stock(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        assert item.stock_in_warehouse(warehouse) == Decimal("100.00")

    def test_re_confirming_replaces_rather_than_doubles(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        so.reserve_stock()
        assert so.reservations.count() == 1

    def test_delivery_releases_the_reservation(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        so.status = "Submitted"
        so.save()
        so.deliver_stock()
        assert so.reservations.count() == 0
        assert item.stock_in_warehouse(warehouse) == Decimal("90.00")

    def test_confirmation_through_the_api_reserves(
        self, auth_client, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        response = auth_client.patch(
            f"/api/selling/sales-orders/{so.pk}/", {"status": "Submitted"}, format="json"
        )
        assert response.status_code == 200
        assert so.reservations.count() == 1


@pytest.mark.django_db
class TestSalesAndProductionShareReservations:
    """Production and sales must net against each other, or both commit the
    same units."""

    def test_production_reservation_blocks_a_sale(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 10)
        finished = Item.objects.create(company=company, item_code="FG", item_name="FG")
        bom = BOM.objects.create(company=company, item=finished, bom_name="B", quantity=1)
        BOMItem.objects.create(bom=bom, item=item, qty=1, rate=10)
        wo = WorkOrder.objects.create(
            company=company, branch=branch, warehouse=warehouse, bom=bom,
            wo_number="WO-R1", order_date=date.today(),
            item_to_manufacture=finished, qty_to_produce=10, status="Draft",
        )
        wo.release(ignore_bom_approval=True)
        so = order(company, customer, branch, warehouse, item, 10)
        _, backorder = so.reserve_stock()
        assert backorder is not None  # all 10 are promised to production

    def test_sales_reservation_blocks_production(
        self, company, customer, branch, warehouse, item
    ):
        from django.core.exceptions import ValidationError

        stock(company, warehouse, item, 10)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        so.status = "Submitted"
        so.save()

        finished = Item.objects.create(company=company, item_code="FG2", item_name="FG2")
        bom = BOM.objects.create(company=company, item=finished, bom_name="B2", quantity=1)
        BOMItem.objects.create(bom=bom, item=item, qty=1, rate=10)
        wo = WorkOrder.objects.create(
            company=company, branch=branch, warehouse=warehouse, bom=bom,
            wo_number="WO-R2", order_date=date.today(),
            item_to_manufacture=finished, qty_to_produce=10, status="Draft",
        )
        with pytest.raises(ValidationError, match="Insufficient raw materials"):
            wo.release(ignore_bom_approval=True)


@pytest.mark.django_db
class TestBackorders:
    """SAL-RULE-004."""

    def test_shortage_creates_a_backorder_for_the_missing_qty(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 4)
        so = order(company, customer, branch, warehouse, item, 10)
        reserved, backorder = so.reserve_stock()
        assert backorder is not None
        assert backorder.backorder_of == so
        assert backorder.items.first().qty == Decimal("6.00")

    def test_available_portion_is_still_reserved(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 4)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        assert so.reservations.first().qty == Decimal("4.00")

    def test_original_line_records_what_was_backordered(
        self, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 4)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        assert so.items.first().backordered_qty == Decimal("6.00")

    def test_zero_stock_backorders_everything(
        self, company, customer, branch, warehouse, item
    ):
        so = order(company, customer, branch, warehouse, item, 10)
        reserved, backorder = so.reserve_stock()
        assert reserved == 0
        assert backorder.items.first().qty == Decimal("10.00")

    def test_backorder_stays_draft(self, company, customer, branch, warehouse, item):
        """Confirming it would try to reserve stock that by definition isn't
        there, and would loop."""
        so = order(company, customer, branch, warehouse, item, 10)
        _, backorder = so.reserve_stock()
        assert backorder.status == "Draft"

    def test_backorder_number_is_derived_and_unique(
        self, company, customer, branch, warehouse, item
    ):
        so = order(company, customer, branch, warehouse, item, 10, "SO-BO")
        _, first = so.reserve_stock()
        assert first.so_number == "SO-BO-BO1"
        stock(company, warehouse, item, 0)
        _, second = so.reserve_stock()
        assert second.so_number == "SO-BO-BO2"

    def test_no_shortage_no_backorder(self, company, customer, branch, warehouse, item):
        stock(company, warehouse, item, 100)
        so = order(company, customer, branch, warehouse, item, 10)
        _, backorder = so.reserve_stock()
        assert backorder is None

    def test_backorder_carries_the_original_price(
        self, company, customer, branch, warehouse, item
    ):
        so = order(company, customer, branch, warehouse, item, 10)
        _, backorder = so.reserve_stock()
        assert backorder.items.first().rate == Decimal("10.00")

    def test_availability_endpoint(
        self, auth_client, company, customer, branch, warehouse, item
    ):
        stock(company, warehouse, item, 4)
        so = order(company, customer, branch, warehouse, item, 10)
        so.reserve_stock()
        response = auth_client.get(f"/api/selling/sales-orders/{so.pk}/availability/")
        assert response.status_code == 200
        assert response.data["lines"][0]["backordered"] == "6.00"
        assert len(response.data["backorders"]) == 1
