"""Tests for INV-RULE-004 / BRN-CTRL-003 (stock transfers between warehouses
and branches) and CRM-RULE-002 (opportunity stage progression) from
ERP_Complete_System.xlsx.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.crm.models import Opportunity
from apps.inventory.models import Item, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="tr@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="TR Co", code="TR-CO")


@pytest.fixture
def riyadh(company):
    return Branch.objects.create(company=company, name="Riyadh", code="TR-R", address="Riyadh")


@pytest.fixture
def jeddah(company):
    return Branch.objects.create(company=company, name="Jeddah", code="TR-J", address="Jeddah")


@pytest.fixture
def wh_r(riyadh):
    return Warehouse.objects.get(branch=riyadh)


@pytest.fixture
def wh_j(jeddah):
    return Warehouse.objects.get(branch=jeddah)


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="T-1", item_name="Crate")


def receipt(company, wh, item, qty):
    return StockEntry.objects.create(
        company=company, warehouse=wh, item=item, entry_type="Receipt",
        quantity=qty, rate=10,
    )


def transfer(company, item, src, dst, qty):
    return StockEntry.objects.create(
        company=company, warehouse=src, source_warehouse=src, target_warehouse=dst,
        item=item, entry_type="Transfer", quantity=qty, rate=10,
    )


@pytest.mark.django_db
class TestStockTransfers:
    """INV-RULE-004. Transfers were completely inert: the type and the
    source/target fields existed, but nothing read them."""

    def test_transfer_moves_stock_between_warehouses(self, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 100)
        transfer(company, item, wh_r, wh_j, 30)
        assert item.stock_in_warehouse(wh_r) == Decimal("70.00")
        assert item.stock_in_warehouse(wh_j) == Decimal("30.00")

    def test_company_total_is_unchanged_by_a_transfer(self, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 100)
        transfer(company, item, wh_r, wh_j, 30)
        assert item.stock_quantity == 100

    def test_warehouse_occupancy_reflects_transfers(self, company, item, wh_r, wh_j):
        wh_r.capacity = 100
        wh_r.save()
        receipt(company, wh_r, item, 100)
        assert wh_r.occupancy_rate == 100.0
        transfer(company, item, wh_r, wh_j, 40)
        assert wh_r.occupancy_rate == 60.0

    def test_transfer_needs_both_ends(self, company, item, wh_r):
        e = StockEntry(
            company=company, warehouse=wh_r, item=item, entry_type="Transfer",
            quantity=5, rate=10,
        )
        with pytest.raises(ValidationError, match="source and a target"):
            e.clean()

    def test_transfer_to_itself_rejected(self, company, item, wh_r):
        e = StockEntry(
            company=company, warehouse=wh_r, source_warehouse=wh_r, target_warehouse=wh_r,
            item=item, entry_type="Transfer", quantity=5, rate=10,
        )
        with pytest.raises(ValidationError, match="must differ"):
            e.clean()

    def test_cannot_transfer_more_than_the_source_holds(self, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 10)
        e = StockEntry(
            company=company, warehouse=wh_r, source_warehouse=wh_r, target_warehouse=wh_j,
            item=item, entry_type="Transfer", quantity=50, rate=10,
        )
        with pytest.raises(ValidationError, match="only 10"):
            e.clean()

    def test_chained_transfers_accumulate(self, company, item, wh_r, wh_j, riyadh):
        wh_r2 = Warehouse.objects.create(branch=riyadh, name="R2", code="TR-R2")
        receipt(company, wh_r, item, 100)
        transfer(company, item, wh_r, wh_j, 60)
        transfer(company, item, wh_j, wh_r2, 20)
        assert item.stock_in_warehouse(wh_r) == Decimal("40.00")
        assert item.stock_in_warehouse(wh_j) == Decimal("40.00")
        assert item.stock_in_warehouse(wh_r2) == Decimal("20.00")

    def test_api_rejects_an_over_transfer(self, auth_client, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 5)
        response = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": wh_r.pk, "source_warehouse": wh_r.pk,
            "target_warehouse": wh_j.pk, "item": item.pk, "entry_type": "Transfer",
            "quantity": "50", "rate": "10",
        }, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestInterBranchAudit:
    """BRN-CTRL-003."""

    def test_inter_branch_transfer_flagged(self, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 100)
        e = transfer(company, item, wh_r, wh_j, 10)
        assert e.is_inter_branch is True

    def test_intra_branch_transfer_not_flagged(self, company, item, wh_r, riyadh):
        wh_r2 = Warehouse.objects.create(branch=riyadh, name="R2", code="TR-R3")
        receipt(company, wh_r, item, 100)
        e = transfer(company, item, wh_r, wh_r2, 10)
        assert e.is_inter_branch is False

    def test_audit_endpoint_lists_only_inter_branch(
        self, auth_client, company, item, wh_r, wh_j, riyadh
    ):
        wh_r2 = Warehouse.objects.create(branch=riyadh, name="R2", code="TR-R4")
        receipt(company, wh_r, item, 100)
        transfer(company, item, wh_r, wh_j, 10)   # inter-branch
        transfer(company, item, wh_r, wh_r2, 5)   # intra-branch
        response = auth_client.get("/api/core/inter-branch-transfers/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["transfers"][0]["from_branch"] == "Riyadh"
        assert response.data["transfers"][0]["to_branch"] == "Jeddah"

    def test_audit_is_company_scoped(self, api_client, django_user_model, company, item, wh_r, wh_j):
        receipt(company, wh_r, item, 100)
        transfer(company, item, wh_r, wh_j, 10)
        outsider = django_user_model.objects.create_user(
            email="outsider3@x.com", password="testpass123"
        )
        api_client.force_authenticate(user=outsider)
        response = api_client.get("/api/core/inter-branch-transfers/")
        assert response.data["count"] == 0


@pytest.mark.django_db
class TestOpportunityStages:
    """CRM-RULE-002."""

    @pytest.fixture
    def opp(self, company):
        return Opportunity.objects.create(
            company=company, opportunity_name="Big deal", status="Open"
        )

    def test_forward_step_allowed_with_required_fields(self, opp):
        opp.expected_amount = Decimal("1000")
        opp.closing_date = date.today()
        opp.check_stage_transition("Quotation")

    def test_missing_required_fields_blocks_the_stage(self, opp):
        with pytest.raises(ValidationError, match="requires"):
            opp.check_stage_transition("Quotation")

    def test_cannot_skip_straight_to_converted(self, opp):
        opp.expected_amount = Decimal("1000")
        opp.closing_date = date.today()
        opp.customer_name = "Acme"
        with pytest.raises(ValidationError, match="Cannot move"):
            opp.check_stage_transition("Converted")

    def test_lost_is_reachable_from_open(self, opp):
        opp.check_stage_transition("Lost")

    def test_lost_is_terminal(self, opp):
        opp.status = "Lost"
        with pytest.raises(ValidationError, match="Allowed: none"):
            opp.check_stage_transition("Open")

    def test_converted_is_terminal(self, opp):
        opp.status = "Converted"
        with pytest.raises(ValidationError, match="Allowed: none"):
            opp.check_stage_transition("Quotation")

    def test_quotation_to_converted_needs_a_customer(self, opp):
        opp.status = "Quotation"
        opp.expected_amount = Decimal("1000")
        opp.closing_date = date.today()
        with pytest.raises(ValidationError, match="customer_name"):
            opp.check_stage_transition("Converted")

    def test_same_stage_is_a_noop(self, opp):
        opp.check_stage_transition("Open")

    def test_api_blocks_an_illegal_jump(self, auth_client, opp):
        response = auth_client.patch(
            f"/api/crm/opportunities/{opp.pk}/", {"status": "Converted"}, format="json"
        )
        assert response.status_code == 400
        opp.refresh_from_db()
        assert opp.status == "Open"
