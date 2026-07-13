"""Pytest tests for the Selling module (apps.selling): the sales order
cycle from draft to stock delivery. Previously untested (P1 #4 follow-up).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.selling.models import Customer, SalesOrder, SalesOrderItem, SalesTaxCharge


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="sales@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Selling Co", code="SELL-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main Branch", code="MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.create(branch=branch, name="Main WH", code="MWH")


@pytest.fixture
def customer(company):
    return Customer.objects.create(company=company, name="Client A")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="SKU-100", item_name="Widget", standard_rate=50)


@pytest.fixture
def sales_order(company, customer, branch, warehouse):
    return SalesOrder.objects.create(
        company=company,
        customer=customer,
        so_number="SO-001",
        transaction_date=date(2026, 1, 1),
        branch=branch,
        warehouse=warehouse,
    )


@pytest.mark.django_db
class TestSalesOrderTotals:
    def test_recalculate_totals_sums_items_minus_discount_plus_tax(self, sales_order, item):
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=10, rate=50)
        SalesTaxCharge.objects.create(sales_order=sales_order, tax_rate=15, tax_amount=75)
        sales_order.discount = 50
        sales_order.save()
        sales_order.recalculate_totals()
        sales_order.refresh_from_db()
        assert sales_order.total_qty == 10
        assert sales_order.total_amount == 500
        # (500 - 50 discount) + 75 tax = 525
        assert sales_order.grand_total == 525

    def test_outstanding_amount_reflects_payments(self, sales_order, item):
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=2, rate=100)
        sales_order.recalculate_totals()
        sales_order.refresh_from_db()
        sales_order.payments.create(payment_date=date(2026, 1, 2), amount=80)
        assert sales_order.total_paid == 80
        assert sales_order.outstanding_amount == sales_order.grand_total - 80


@pytest.mark.django_db
class TestSalesOrderItemAmount:
    def test_amount_is_computed_from_qty_times_rate(self, sales_order, item):
        line = SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=3, rate=Decimal("12.50"))
        assert line.amount == Decimal("37.50")


@pytest.mark.django_db
class TestDeliverStock:
    def test_delivering_with_sufficient_stock_creates_issue_entries(
        self, company, branch, warehouse, sales_order, item
    ):
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=20, rate=50,
        )
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=5, rate=50)
        sales_order.deliver_stock()
        issue = StockEntry.objects.get(item=item, entry_type="Issue")
        assert issue.quantity == 5
        line = sales_order.items.get(item=item)
        assert line.delivered_qty == 5

    def test_delivering_with_insufficient_stock_raises_and_creates_nothing(
        self, company, branch, warehouse, sales_order, item
    ):
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=2, rate=50,
        )
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=5, rate=50)
        with pytest.raises(ValidationError):
            sales_order.deliver_stock()
        assert not StockEntry.objects.filter(item=item, entry_type="Issue").exists()

    def test_delivering_all_or_nothing_across_multiple_lines(
        self, company, branch, warehouse, sales_order, item
    ):
        item2 = Item.objects.create(company=company, item_code="SKU-101", item_name="Gadget", standard_rate=20)
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=10, rate=50,
        )
        # item2 has NO stock at all.
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=5, rate=50)
        SalesOrderItem.objects.create(sales_order=sales_order, item=item2, qty=1, rate=20)
        with pytest.raises(ValidationError):
            sales_order.deliver_stock()
        # Item with enough stock must NOT have been partially issued either.
        assert not StockEntry.objects.filter(item=item, entry_type="Issue").exists()

    def test_delivering_without_warehouse_raises(self, company, customer, item):
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-NOWH",
            transaction_date=date(2026, 1, 1),
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=1, rate=10)
        with pytest.raises(ValidationError):
            so.deliver_stock()

    def test_delivering_with_no_line_items_raises(self, company, branch, warehouse, sales_order):
        with pytest.raises(ValidationError):
            sales_order.deliver_stock()


@pytest.mark.django_db
class TestSalesOrderAPI:
    def test_submit_then_deliver_via_status_transition(self, auth_client, sales_order, item, company, branch, warehouse):
        StockEntry.objects.create(
            company=company, branch=branch, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=10, rate=50,
        )
        SalesOrderItem.objects.create(sales_order=sales_order, item=item, qty=3, rate=50)

        r1 = auth_client.patch(f"/api/selling/sales-orders/{sales_order.id}/", {"status": "Submitted"})
        assert r1.status_code == status.HTTP_200_OK

        r2 = auth_client.patch(f"/api/selling/sales-orders/{sales_order.id}/", {"status": "Delivered"})
        assert r2.status_code == status.HTTP_200_OK
        assert StockEntry.objects.filter(item=item, entry_type="Issue").exists()

    def test_invalid_status_transition_rejected(self, auth_client, sales_order):
        response = auth_client.patch(
            f"/api/selling/sales-orders/{sales_order.id}/", {"status": "Delivered"}
        )
        # Draft -> Delivered directly is not an allowed transition.
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/selling/sales-orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
