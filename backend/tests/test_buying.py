"""Pytest tests for the Buying/Purchasing module (apps.buying): the
purchase order cycle from draft to stock receipt. Previously untested
(P1 #4 follow-up).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, PurchaseOrderItem, PurchaseTaxCharge, Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="purchasing@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Buying Co", code="BUY-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main Branch", code="MB2", address="Jeddah")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.create(branch=branch, name="Main WH", code="MWH2")


@pytest.fixture
def supplier(company):
    return Supplier.objects.create(company=company, name="Supplier A")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="SKU-200", item_name="Raw Material", standard_rate=30)


@pytest.fixture
def purchase_order(company, supplier, branch, warehouse):
    return PurchaseOrder.objects.create(
        company=company,
        supplier=supplier,
        po_number="PO-001",
        transaction_date=date(2026, 1, 1),
        branch=branch,
        warehouse=warehouse,
    )


@pytest.fixture
def approver(company, django_user_model):
    """A Manager-level approver. PRC-CTRL-005 requires every PO to be signed off
    by a role authorised for its value; the smallest tier is Manager."""
    from apps.hr.models import Department, Employee
    from apps.rbac.models import Role, RoleAssignment

    user = django_user_model.objects.create_user(
        email="po.manager@nexus.com", password="testpass123"
    )
    RoleAssignment.objects.create(
        user=user, role=Role.objects.create(name="Manager", permissions={})
    )
    dept = Department.objects.create(company=company, name="Procurement")
    return Employee.objects.create(
        company=company, department=dept, employee_id="APR-1",
        first_name="Po", last_name="Manager", date_of_joining=date(2025, 1, 1), user=user,
    )


@pytest.mark.django_db
class TestPurchaseOrderTotals:
    def test_recalculate_totals_sums_items_minus_discount_plus_tax(self, purchase_order, item):
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=20, rate=30)
        PurchaseTaxCharge.objects.create(purchase_order=purchase_order, tax_rate=15, tax_amount=90)
        purchase_order.discount = 100
        purchase_order.save()
        purchase_order.recalculate_totals()
        purchase_order.refresh_from_db()
        assert purchase_order.total_qty == 20
        assert purchase_order.total_amount == 600
        # (600 - 100 discount) + 90 tax = 590
        assert purchase_order.grand_total == 590

    def test_totals_recalculate_automatically_when_a_line_item_is_added(self, purchase_order, item):
        # No manual recalculate_totals() call — this must happen via signal.
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=3, rate=30)
        purchase_order.refresh_from_db()
        assert purchase_order.total_amount == 90
        assert purchase_order.grand_total == 90

    def test_outstanding_amount_reflects_payments(self, purchase_order, item):
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=1, rate=200)
        purchase_order.recalculate_totals()
        purchase_order.refresh_from_db()
        purchase_order.payments.create(payment_date=date(2026, 1, 2), amount=50)
        assert purchase_order.total_paid == 50
        assert purchase_order.outstanding_amount == purchase_order.grand_total - 50


@pytest.mark.django_db
class TestPurchaseOrderItemAmount:
    def test_amount_is_computed_from_qty_times_rate(self, purchase_order, item):
        line = PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=4, rate=Decimal("7.25"))
        assert line.amount == Decimal("29.00")


@pytest.mark.django_db
class TestReceiveStock:
    def test_receiving_creates_receipt_entries_and_marks_lines_received(
        self, company, branch, warehouse, purchase_order, item
    ):
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=15, rate=30)
        purchase_order.receive_stock()
        receipt = StockEntry.objects.get(item=item, entry_type="Receipt")
        assert receipt.quantity == 15
        line = purchase_order.items.get(item=item)
        assert line.received_qty == 15
        assert item.stock_quantity == 15

    def test_receiving_without_warehouse_raises(self, company, supplier, item):
        po = PurchaseOrder.objects.create(
            company=company, supplier=supplier, po_number="PO-NOWH",
            transaction_date=date(2026, 1, 1),
        )
        PurchaseOrderItem.objects.create(purchase_order=po, item=item, qty=1, rate=10)
        with pytest.raises(ValidationError):
            po.receive_stock()

    def test_receiving_with_no_line_items_raises(self, purchase_order):
        with pytest.raises(ValidationError):
            purchase_order.receive_stock()

    def test_receiving_multiple_lines_increases_stock_for_each_item(
        self, company, branch, warehouse, purchase_order, item
    ):
        item2 = Item.objects.create(company=company, item_code="SKU-201", item_name="Component", standard_rate=5)
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=10, rate=30)
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item2, qty=50, rate=5)
        purchase_order.receive_stock()
        assert item.stock_quantity == 10
        assert item2.stock_quantity == 50


@pytest.mark.django_db
class TestPurchaseOrderAPI:
    def test_submit_then_receive_via_status_transition(
        self, auth_client, purchase_order, item, company, branch, warehouse, approver
    ):
        PurchaseOrderItem.objects.create(purchase_order=purchase_order, item=item, qty=5, rate=30)
        purchase_order.recalculate_totals()

        r1 = auth_client.patch(
            f"/api/buying/purchase-orders/{purchase_order.id}/",
            {"status": "Submitted", "approved_by": approver.pk},
        )
        assert r1.status_code == status.HTTP_200_OK

        r2 = auth_client.patch(f"/api/buying/purchase-orders/{purchase_order.id}/", {"status": "Received"})
        assert r2.status_code == status.HTTP_200_OK
        assert StockEntry.objects.filter(item=item, entry_type="Receipt").exists()

    def test_invalid_status_transition_rejected(self, auth_client, purchase_order):
        response = auth_client.patch(
            f"/api/buying/purchase-orders/{purchase_order.id}/", {"status": "Received"}
        )
        # Draft -> Received directly is not an allowed transition.
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/buying/purchase-orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
