"""Multi-level approval / release strategies.

A document routes through an ordered chain of release levels chosen from its type
and amount, each level requiring a role, until every level signs off — the SAP
release-strategy shape. Enforces order, role, segregation of duties (a requester
can't release their own document), and rejection stopping the chain.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.approvals.models import (
    ApprovalRequest, ReleaseLevel, ReleaseStrategy,
)
from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import CompanyProfile
from apps.rbac.models import Role, RoleAssignment
from apps.tenants.models import Tenant


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="T", slug="t", subdomain="t")


@pytest.fixture
def roles(db):
    return (
        Role.objects.create(name="Manager"),
        Role.objects.create(name="Finance"),
        Role.objects.create(name="CEO"),
    )


@pytest.fixture
def users(db, django_user_model, tenant, roles):
    mgr = django_user_model.objects.create_user(email="m@x.com", password="x", tenant=tenant)
    fin = django_user_model.objects.create_user(email="f@x.com", password="x", tenant=tenant)
    ceo = django_user_model.objects.create_user(email="c@x.com", password="x", tenant=tenant)
    req = django_user_model.objects.create_user(email="r@x.com", password="x", tenant=tenant)
    RoleAssignment.objects.create(user=mgr, role=roles[0])
    RoleAssignment.objects.create(user=fin, role=roles[1])
    RoleAssignment.objects.create(user=ceo, role=roles[2])
    return {"mgr": mgr, "fin": fin, "ceo": ceo, "req": req}


@pytest.fixture
def big_strategy(db, tenant, roles):
    s = ReleaseStrategy.objects.create(
        name="Large PO", document_type="purchase_order",
        min_amount=Decimal("100000"), tenant=tenant,
    )
    ReleaseLevel.objects.create(strategy=s, sequence=1, role=roles[0])
    ReleaseLevel.objects.create(strategy=s, sequence=2, role=roles[1])
    ReleaseLevel.objects.create(strategy=s, sequence=3, role=roles[2])
    return s


@pytest.fixture
def po(db):
    c = CompanyProfile.objects.create(name="A", code="AC")
    sup = Supplier.objects.create(company=c, name="S")
    return PurchaseOrder.objects.create(
        company=c, supplier=sup, po_number="PO1", transaction_date="2026-01-01"
    )


@pytest.mark.django_db
class TestStrategyResolution:
    def test_highest_matching_min_amount_wins(self, tenant, roles):
        big = ReleaseStrategy.objects.create(name="Big", document_type="purchase_order",
                                             min_amount=Decimal("100000"), tenant=tenant)
        med = ReleaseStrategy.objects.create(name="Med", document_type="purchase_order",
                                             min_amount=Decimal("10000"), tenant=tenant)
        assert ReleaseStrategy.resolve("purchase_order", Decimal("500000")) == big
        assert ReleaseStrategy.resolve("purchase_order", Decimal("15000")) == med

    def test_below_all_thresholds_needs_no_strategy(self, tenant):
        ReleaseStrategy.objects.create(name="Med", document_type="purchase_order",
                                       min_amount=Decimal("10000"), tenant=tenant)
        assert ReleaseStrategy.resolve("purchase_order", Decimal("500")) is None


@pytest.mark.django_db
class TestChainLogic:
    def test_open_builds_one_step_per_level(self, big_strategy, po, users, tenant):
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        assert req.steps.count() == 3
        assert req.current_step.level.sequence == 1

    def test_requester_cannot_release_own_document(self, big_strategy, po, users, tenant):
        from django.core.exceptions import ValidationError
        # Make the requester also hold the first role.
        RoleAssignment.objects.create(user=users["req"], role=big_strategy.levels.first().role)
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        with pytest.raises(ValidationError):
            req.act(users["req"], approve=True)

    def test_levels_must_be_released_in_order(self, big_strategy, po, users, tenant):
        from django.core.exceptions import ValidationError
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        # Finance (level 2) can't go before Manager (level 1).
        with pytest.raises(ValidationError):
            req.act(users["fin"], approve=True)

    def test_full_chain_completes(self, big_strategy, po, users, tenant):
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        req.act(users["mgr"], approve=True)
        req.act(users["fin"], approve=True)
        req.act(users["ceo"], approve=True)
        assert req.status == "approved"
        assert req.current_step is None

    def test_rejection_stops_the_chain(self, big_strategy, po, users, tenant):
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        req.act(users["mgr"], approve=True)
        req.act(users["fin"], approve=False, comment="over budget")
        assert req.status == "rejected"
        assert req.current_step is None  # CEO never gets asked

    def test_wrong_role_cannot_release(self, big_strategy, po, users, tenant):
        from django.core.exceptions import ValidationError
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        # CEO holds a role, but not level 1's role.
        with pytest.raises(ValidationError):
            req.act(users["ceo"], approve=True)


@pytest.mark.django_db
class TestApprovalAPI:
    def _client(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_create_strategy_with_levels(self, tenant, roles):
        admin = self._client_admin(tenant)
        r = admin.post("/api/approvals/strategies/", {
            "name": "Large", "document_type": "purchase_order",
            "min_amount": "100000", "tenant": tenant.id,
            "levels": [{"sequence": 1, "role": roles[0].id},
                       {"sequence": 2, "role": roles[1].id}],
        }, format="json")
        assert r.status_code == 201, r.data
        assert len(r.data["levels"]) == 2

    def _client_admin(self, tenant):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser(
            email="admin@x.com", password="x", tenant=tenant)
        return self._client(admin)

    def test_pending_and_act_flow(self, big_strategy, po, users, tenant):
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        mgr_c = self._client(users["mgr"])
        fin_c = self._client(users["fin"])
        # Manager sees it pending; finance does not yet.
        assert len(mgr_c.get("/api/approvals/requests/pending/").data) == 1
        assert len(fin_c.get("/api/approvals/requests/pending/").data) == 0
        # Manager approves; now finance sees it.
        r = mgr_c.post(f"/api/approvals/requests/{req.id}/act/", {"approve": True}, format="json")
        assert r.data["current_sequence"] == 2
        assert len(fin_c.get("/api/approvals/requests/pending/").data) == 1

    def test_act_rejects_requester(self, big_strategy, po, users, tenant):
        RoleAssignment.objects.create(user=users["req"], role=big_strategy.levels.first().role)
        req = ApprovalRequest.open_for(po, "purchase_order", Decimal("500000"),
                                       requested_by=users["req"], tenant=tenant)
        c = self._client(users["req"])
        r = c.post(f"/api/approvals/requests/{req.id}/act/", {"approve": True}, format="json")
        assert r.status_code == 400
