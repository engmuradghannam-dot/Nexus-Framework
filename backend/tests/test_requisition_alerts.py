"""Tests for PRC-RULE-001 (auto PO from requisition), PRC-RULE-002 (delivery
date alert) and PRC-RULE-005 (supplier contract expiry) from
ERP_Complete_System.xlsx.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.buying.models import (
    PurchaseOrder,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    Supplier,
)
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="pr@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="PR Co", code="PR-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="PR-MB", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def acme(company):
    return Supplier.objects.create(company=company, name="Acme")


@pytest.fixture
def globex(company):
    return Supplier.objects.create(company=company, name="Globex")


def item(company, code, supplier=None, rate=10):
    return Item.objects.create(
        company=company, item_code=code, item_name=code,
        supplier=supplier, standard_rate=rate,
    )


def requisition(company, branch, warehouse, number="PR-1", status="Approved"):
    return PurchaseRequisition.objects.create(
        company=company, branch=branch, warehouse=warehouse, pr_number=number,
        transaction_date=date.today(), required_by=date.today() + timedelta(days=14),
        status=status,
    )


@pytest.mark.django_db
class TestRequisitionToPO:
    """PRC-RULE-001."""

    def test_groups_lines_by_preferred_supplier(self, company, branch, warehouse, acme, globex):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=5)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A2", acme), qty=3)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "G1", globex), qty=2)
        created, unsourced = pr.generate_purchase_orders()
        assert len(created) == 2 and unsourced == []
        by_supplier = {po.supplier.name: po.items.count() for po in created}
        assert by_supplier == {"Acme": 2, "Globex": 1}

    def test_unapproved_requisition_cannot_raise_pos(self, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse, status="Draft")
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        with pytest.raises(ValidationError, match="approved requisition"):
            pr.generate_purchase_orders()

    def test_items_without_a_preferred_supplier_are_reported(
        self, company, branch, warehouse, acme
    ):
        """Silently dropping them is how a requisition goes half-ordered."""
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "ORPHAN"), qty=1)
        created, unsourced = pr.generate_purchase_orders()
        assert len(created) == 1
        assert unsourced == ["ORPHAN"]

    def test_status_stays_approved_while_lines_are_unsourced(
        self, company, branch, warehouse, acme
    ):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "ORPHAN"), qty=1)
        pr.generate_purchase_orders()
        pr.refresh_from_db()
        assert pr.status == "Approved"

    def test_status_moves_to_ordered_when_fully_sourced(self, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        pr.generate_purchase_orders()
        pr.refresh_from_db()
        assert pr.status == "Ordered"

    def test_generated_po_is_a_draft_needing_its_own_approval(
        self, company, branch, warehouse, acme
    ):
        """PRC-CTRL-005 still applies: approving the request isn't approving
        the spend."""
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        created, _ = pr.generate_purchase_orders()
        assert created[0].status == "Draft"
        assert created[0].approved_by is None

    def test_line_rate_falls_back_to_the_standard_rate(self, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(
            requisition=pr, item=item(company, "A1", acme, rate=77), qty=1
        )
        created, _ = pr.generate_purchase_orders()
        assert created[0].items.first().rate == Decimal("77.00")

    def test_line_rate_wins_when_supplied(self, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(
            requisition=pr, item=item(company, "A1", acme, rate=77), qty=1, rate=Decimal("50")
        )
        created, _ = pr.generate_purchase_orders()
        assert created[0].items.first().rate == Decimal("50.00")

    def test_lines_are_linked_back_to_their_po(self, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse)
        line = PurchaseRequisitionItem.objects.create(
            requisition=pr, item=item(company, "A1", acme), qty=1
        )
        created, _ = pr.generate_purchase_orders()
        line.refresh_from_db()
        assert line.purchase_order == created[0]

    def test_empty_requisition_rejected(self, company, branch, warehouse):
        pr = requisition(company, branch, warehouse)
        with pytest.raises(ValidationError, match="no lines"):
            pr.generate_purchase_orders()

    def test_api_action(self, auth_client, company, branch, warehouse, acme):
        pr = requisition(company, branch, warehouse)
        PurchaseRequisitionItem.objects.create(requisition=pr, item=item(company, "A1", acme), qty=1)
        response = auth_client.post(
            f"/api/buying/purchase-requisitions/{pr.pk}/generate_purchase_orders/"
        )
        assert response.status_code == 200
        assert len(response.data["created"]) == 1
        assert response.data["status"] == "Ordered"


@pytest.mark.django_db
class TestDeliveryAlert:
    """PRC-RULE-002: 3 days out."""

    def po(self, company, acme, branch, days, number, status="Submitted"):
        return PurchaseOrder.objects.create(
            company=company, supplier=acme, branch=branch, po_number=number,
            transaction_date=date.today(), status=status,
            required_by=None if days is None else date.today() + timedelta(days=days),
        )

    def test_due_within_three_days_alerts(self, company, acme, branch):
        assert self.po(company, acme, branch, 2, "PO-D1").delivery_due_soon is True

    def test_further_out_does_not_alert(self, company, acme, branch):
        assert self.po(company, acme, branch, 10, "PO-D2").delivery_due_soon is False

    def test_overdue_is_flagged(self, company, acme, branch):
        p = self.po(company, acme, branch, -5, "PO-D3")
        assert p.delivery_due_soon is True and p.delivery_overdue is True

    def test_received_order_cannot_be_late(self, company, acme, branch):
        p = self.po(company, acme, branch, -5, "PO-D4", status="Received")
        assert p.delivery_due_soon is False and p.delivery_overdue is False

    def test_no_required_by_no_alert(self, company, acme, branch):
        assert self.po(company, acme, branch, None, "PO-D5").delivery_due_soon is False


@pytest.mark.django_db
class TestContractExpiry:
    """PRC-RULE-005: 60-day renewal window."""

    def test_expiring_within_60_days_alerts(self, company):
        s = Supplier.objects.create(
            company=company, name="Soon", contract_end=date.today() + timedelta(days=30)
        )
        assert s.contract_expires_soon is True and s.contract_expired is False

    def test_beyond_60_days_does_not_alert(self, company):
        s = Supplier.objects.create(
            company=company, name="Later", contract_end=date.today() + timedelta(days=120)
        )
        assert s.contract_expires_soon is False

    def test_already_expired_is_flagged(self, company):
        s = Supplier.objects.create(
            company=company, name="Gone", contract_end=date.today() - timedelta(days=1)
        )
        assert s.contract_expires_soon is True and s.contract_expired is True

    def test_no_contract_no_alert(self, company):
        s = Supplier.objects.create(company=company, name="None")
        assert s.days_to_contract_end is None and s.contract_expires_soon is False


@pytest.mark.django_db
class TestAlertsEndpoint:
    def test_lists_both_alert_types(self, auth_client, company, acme, branch):
        acme.contract_end = date.today() + timedelta(days=10)
        acme.save()
        PurchaseOrder.objects.create(
            company=company, supplier=acme, branch=branch, po_number="PO-AL-1",
            transaction_date=date.today(), status="Submitted",
            required_by=date.today() + timedelta(days=1),
        )
        response = auth_client.get("/api/buying/alerts/")
        assert response.status_code == 200
        assert len(response.data["deliveries_due"]) == 1
        assert len(response.data["contracts_expiring"]) == 1

    def test_scoped_to_the_callers_companies(self, api_client, django_user_model, company, acme):
        acme.contract_end = date.today() + timedelta(days=5)
        acme.save()
        outsider = django_user_model.objects.create_user(
            email="outsider2@x.com", password="testpass123"
        )
        api_client.force_authenticate(user=outsider)
        response = api_client.get("/api/buying/alerts/")
        assert response.data["contracts_expiring"] == []
