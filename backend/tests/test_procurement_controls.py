"""Tests for the procurement rules/controls from ERP_Complete_System.xlsx.

Covers PRC-CTRL-005 (tiered approval), FIN-CTRL-002 (segregation of duties),
INV-CTRL-003 (goods receipt validation), PRC-CTRL-001 (three-way match) and
PRC-RULE-004 (price variance).
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.buying.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
)
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.hr.models import Department, Employee
from apps.inventory.models import Item, StockEntry
from apps.rbac.models import Role, RoleAssignment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Proc Co", code="PROC-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="PRC-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def supplier(company):
    return Supplier.objects.create(company=company, name="Vendor")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="P-1", item_name="Part", standard_rate=10)


@pytest.fixture
def department(company):
    return Department.objects.create(company=company, name="Procurement")


def make_approver(company, department, django_user_model, role_name, email):
    user = django_user_model.objects.create_user(email=email, password="testpass123")
    RoleAssignment.objects.create(
        user=user, role=Role.objects.create(name=role_name, permissions={})
    )
    return Employee.objects.create(
        company=company, department=department, employee_id=f"E-{role_name}",
        first_name=role_name, last_name="Approver",
        date_of_joining=date(2025, 1, 1), user=user,
    )


@pytest.fixture
def manager(company, department, django_user_model):
    return make_approver(company, department, django_user_model, "Manager", "mgr@nexus.com")


@pytest.fixture
def cfo(company, department, django_user_model):
    return make_approver(company, department, django_user_model, "CFO", "cfo@nexus.com")


def make_po(company, supplier, branch, warehouse, item, number, qty, rate):
    po = PurchaseOrder.objects.create(
        company=company, supplier=supplier, po_number=number,
        transaction_date=date(2026, 1, 10), branch=branch, warehouse=warehouse,
        status="Draft",
    )
    PurchaseOrderItem.objects.create(purchase_order=po, item=item, qty=qty, rate=rate)
    po.recalculate_totals()
    po.refresh_from_db()
    return po


@pytest.mark.django_db
class TestApprovalHierarchy:
    """PRC-CTRL-005: tiered at 10K / 50K / 100K / 500K."""

    @pytest.mark.parametrize("amount,expected", [
        (5000, "Manager"), (10000, "Manager"),
        (10001, "Director"), (50000, "Director"),
        (50001, "CFO"), (100000, "CFO"),
        (100001, "CEO"), (900000, "CEO"),
    ])
    def test_required_role_by_value(self, company, supplier, branch, warehouse, item, amount, expected):
        po = make_po(company, supplier, branch, warehouse, item, f"PO-T-{amount}", 1, amount)
        assert po.required_approval_role == expected

    def test_unapproved_po_is_rejected(self, company, supplier, branch, warehouse, item):
        po = make_po(company, supplier, branch, warehouse, item, "PO-NA-1", 1, 500)
        with pytest.raises(ValidationError, match="requires approval"):
            po.check_approval()

    def test_manager_can_approve_small_po(self, company, supplier, branch, warehouse, item, manager):
        po = make_po(company, supplier, branch, warehouse, item, "PO-OK-1", 1, 500)
        po.approved_by = manager
        po.check_approval()

    def test_manager_cannot_approve_a_cfo_tier_po(self, company, supplier, branch, warehouse, item, manager):
        po = make_po(company, supplier, branch, warehouse, item, "PO-HI-1", 1, 90000)
        po.approved_by = manager
        with pytest.raises(ValidationError, match="does not hold that authority"):
            po.check_approval()

    def test_senior_role_can_approve_a_lower_tier(self, company, supplier, branch, warehouse, item, cfo):
        po = make_po(company, supplier, branch, warehouse, item, "PO-LO-1", 1, 500)
        po.approved_by = cfo
        po.check_approval()

    def test_fin_ctrl_002_creator_cannot_approve_own_po(
        self, company, supplier, branch, warehouse, item, manager
    ):
        po = make_po(company, supplier, branch, warehouse, item, "PO-SOD-1", 1, 500)
        po.created_by = manager.user
        po.approved_by = manager
        with pytest.raises(ValidationError, match="Segregation of duties"):
            po.check_approval()

    def test_approver_without_user_account_rejected(
        self, company, supplier, branch, warehouse, item, department
    ):
        orphan = Employee.objects.create(
            company=company, department=department, employee_id="E-NOU",
            first_name="No", last_name="User", date_of_joining=date(2025, 1, 1),
        )
        po = make_po(company, supplier, branch, warehouse, item, "PO-NU-1", 1, 500)
        po.approved_by = orphan
        with pytest.raises(ValidationError, match="no linked user account"):
            po.check_approval()


@pytest.mark.django_db
class TestGoodsReceipt:
    """INV-CTRL-003: GRN must match the PO."""

    @pytest.fixture
    def po(self, company, supplier, branch, warehouse, item):
        po = make_po(company, supplier, branch, warehouse, item, "PO-GRN-1", 10, 100)
        po.status = "Submitted"
        po.save()
        return po

    def test_receipt_posts_accepted_qty_to_the_right_warehouse(self, po, item, warehouse, company):
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-1",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=10
        )
        grn.submit()
        assert item.stock_in_warehouse(warehouse) == 10

    def test_rejected_qty_is_not_received_into_stock(self, po, item, warehouse, company):
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-2",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=10,
            qty_rejected=3, rejection_reason="Damaged",
        )
        grn.submit()
        assert item.stock_in_warehouse(warehouse) == 7
        po.refresh_from_db()
        assert po.items.first().accepted_qty == 7

    def test_cannot_receive_more_than_ordered(self, po, warehouse, company):
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-3",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=15
        )
        with pytest.raises(ValidationError, match="exceeds the purchase order"):
            grn.submit()

    def test_partial_receipts_accumulate_and_then_cap(self, po, item, warehouse, company):
        for n, qty in [(1, 6), (2, 4)]:
            grn = GoodsReceipt.objects.create(
                company=company, purchase_order=po, grn_number=f"GRN-P{n}",
                receipt_date=date(2026, 1, 12), warehouse=warehouse,
            )
            GoodsReceiptItem.objects.create(
                goods_receipt=grn, po_item=po.items.first(), qty_received=qty
            )
            grn.submit()
        assert item.stock_in_warehouse(warehouse) == 10
        # a third receipt has nothing left to receive
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-P3",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=1
        )
        with pytest.raises(ValidationError, match="exceeds the purchase order"):
            grn.submit()

    def test_rejected_cannot_exceed_received(self, po, warehouse, company):
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-4",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        with pytest.raises(ValidationError):
            GoodsReceiptItem.objects.create(
                goods_receipt=grn, po_item=po.items.first(), qty_received=5, qty_rejected=6
            )

    def test_nothing_posts_if_any_line_fails(self, po, item, warehouse, company):
        """A receipt is all-or-nothing: a bad line must not leave the good ones
        already in stock."""
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number="GRN-5",
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=99
        )
        with pytest.raises(ValidationError):
            grn.submit()
        assert item.stock_in_warehouse(warehouse) == 0
        assert not StockEntry.objects.filter(item=item).exists()


@pytest.mark.django_db
class TestThreeWayMatch:
    """PRC-CTRL-001: PO vs GRN vs Invoice."""

    @pytest.fixture
    def po(self, company, supplier, branch, warehouse, item):
        po = make_po(company, supplier, branch, warehouse, item, "PO-3W-1", 10, 100)
        po.status = "Submitted"
        po.save()
        return po

    def _receive(self, po, company, warehouse, qty, number):
        grn = GoodsReceipt.objects.create(
            company=company, purchase_order=po, grn_number=number,
            receipt_date=date(2026, 1, 12), warehouse=warehouse,
        )
        GoodsReceiptItem.objects.create(
            goods_receipt=grn, po_item=po.items.first(), qty_received=qty
        )
        grn.submit()

    def test_short_delivery_is_flagged(self, po, company, warehouse):
        self._receive(po, company, warehouse, 7, "GRN-3W-1")
        matched, issues = po.three_way_match()
        assert matched is False
        assert "ordered 10.00, received 7.00" in issues[0]

    def test_full_delivery_and_matching_invoice_passes(self, po, company, warehouse):
        self._receive(po, company, warehouse, 10, "GRN-3W-2")
        from apps.invoicing.models import Invoice

        Invoice.create_from_purchase_order(
            po, invoice_number="PINV-3W-1", invoice_date=date(2026, 1, 13)
        )
        po.refresh_from_db()
        matched, issues = po.three_way_match()
        assert matched is True, issues

    def test_overbilling_is_flagged(self, po, company, warehouse):
        self._receive(po, company, warehouse, 10, "GRN-3W-3")
        PurchaseOrder.objects.filter(pk=po.pk).update(billed_amount=Decimal("5000"))
        po.refresh_from_db()
        matched, issues = po.three_way_match()
        assert matched is False
        assert any("invoiced" in i for i in issues)


@pytest.mark.django_db
class TestPriceVariance:
    """PRC-RULE-004: flag when unit price moves more than 10% vs the last PO."""

    def test_price_jump_is_flagged(self, company, supplier, branch, warehouse, item):
        old = make_po(company, supplier, branch, warehouse, item, "PO-PV-1", 1, 100)
        old.status = "Submitted"
        old.save()
        new = make_po(company, supplier, branch, warehouse, item, "PO-PV-2", 1, 130)
        findings = new.check_price_variance()
        assert len(findings) == 1 and "30.00%" in findings[0]

    def test_small_move_is_not_flagged(self, company, supplier, branch, warehouse, item):
        old = make_po(company, supplier, branch, warehouse, item, "PO-PV-3", 1, 100)
        old.status = "Submitted"
        old.save()
        new = make_po(company, supplier, branch, warehouse, item, "PO-PV-4", 1, 105)
        assert new.check_price_variance() == []

    def test_first_ever_purchase_has_no_baseline(self, company, supplier, branch, warehouse, item):
        po = make_po(company, supplier, branch, warehouse, item, "PO-PV-5", 1, 100)
        assert po.check_price_variance() == []

    def test_draft_pos_do_not_set_the_baseline(self, company, supplier, branch, warehouse, item):
        make_po(company, supplier, branch, warehouse, item, "PO-PV-6", 1, 100)  # stays Draft
        new = make_po(company, supplier, branch, warehouse, item, "PO-PV-7", 1, 500)
        assert new.check_price_variance() == []
