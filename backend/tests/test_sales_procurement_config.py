"""Tests for the remaining configurable rules: SAL-RULE-005 (customer tiers),
CRM-CTRL-004 (commission), CRM-RULE-001 (lead scoring), PRC-CTRL-003 (supplier
scorecard) and PRC-RULE-003 (late penalty).

The sheet gives no numbers for any of these because they belong to Sales and
Procurement, not to the code. Every figure asserted below is one the test
configured, exactly as those teams would.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.buying.models import (
    LatePenaltyTerm,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierScore,
    SupplierScorecard,
    SupplierScorecardCriterion,
)
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.crm.models import Lead, LeadScoringRule
from apps.inventory.models import Item
from apps.selling.models import CommissionRule, Customer, CustomerTier, SalesOrder, SalesOrderItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Cfg2 Co", code="CFG2-CO")


@pytest.fixture
def auth_client(api_client, django_user_model):
    u = django_user_model.objects.create_superuser(email="cfg2@x.com", password="testpass123")
    api_client.force_authenticate(u)
    return api_client


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Main", code="CF2-MB", address="Riyadh")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="C-1", item_name="Thing")


@pytest.fixture
def customer(company):
    return Customer.objects.create(company=company, name="Acme")


def order(company, customer, branch, item, total, number, when=None, status="Submitted", **kw):
    so = SalesOrder.objects.create(
        company=company, customer=customer, so_number=number,
        transaction_date=when or date.today(), branch=branch, status=status, **kw
    )
    SalesOrderItem.objects.create(sales_order=so, item=item, qty=1, rate=total)
    so.recalculate_totals()
    so.refresh_from_db()
    return so


@pytest.mark.django_db
class TestCustomerTiers:
    """SAL-RULE-005."""

    def test_no_tiers_configured_means_no_tier(self, company, customer, branch, item):
        order(company, customer, branch, item, 999999, "SO-T0")
        assert customer.recalculate_tier() is None

    def test_customer_reaches_the_tier_they_qualify_for(self, company, customer, branch, item):
        CustomerTier.objects.create(company=company, name="Silver", min_annual_revenue=Decimal("1000"))
        CustomerTier.objects.create(company=company, name="Gold", min_annual_revenue=Decimal("10000"))
        order(company, customer, branch, item, 5000, "SO-T1")
        assert customer.recalculate_tier().name == "Silver"

    def test_higher_revenue_reaches_the_higher_tier(self, company, customer, branch, item):
        CustomerTier.objects.create(company=company, name="Silver", min_annual_revenue=Decimal("1000"))
        CustomerTier.objects.create(company=company, name="Gold", min_annual_revenue=Decimal("10000"))
        order(company, customer, branch, item, 50000, "SO-T2")
        assert customer.recalculate_tier().name == "Gold"

    def test_qualifying_for_nothing_leaves_no_tier(self, company, customer, branch, item):
        """Not forced into the lowest tier — they qualified for none."""
        CustomerTier.objects.create(company=company, name="Silver", min_annual_revenue=Decimal("1000"))
        order(company, customer, branch, item, 50, "SO-T3")
        assert customer.recalculate_tier() is None

    def test_revenue_outside_the_window_does_not_count(self, company, customer, branch, item):
        CustomerTier.objects.create(
            company=company, name="Silver", min_annual_revenue=Decimal("1000"), window_months=12
        )
        order(company, customer, branch, item, 5000, "SO-T4",
              when=date.today() - timedelta(days=800))
        assert customer.recalculate_tier() is None

    def test_draft_orders_do_not_count(self, company, customer, branch, item):
        CustomerTier.objects.create(company=company, name="Silver", min_annual_revenue=Decimal("1000"))
        order(company, customer, branch, item, 5000, "SO-T5", status="Draft")
        assert customer.recalculate_tier() is None

    def test_changing_the_threshold_changes_the_tier(self, company, customer, branch, item):
        """Proof the threshold comes from Sales, not from the code."""
        tier = CustomerTier.objects.create(
            company=company, name="Silver", min_annual_revenue=Decimal("1000")
        )
        order(company, customer, branch, item, 500, "SO-T6")
        assert customer.recalculate_tier() is None
        tier.min_annual_revenue = Decimal("100")
        tier.save()
        assert customer.recalculate_tier().name == "Silver"


@pytest.mark.django_db
class TestCommission:
    """CRM-CTRL-004."""

    def test_no_rule_means_no_commission_not_a_default_rate(
        self, company, customer, branch, item
    ):
        so = order(company, customer, branch, item, 10000, "SO-C0")
        assert so.commission_amount == Decimal(0)

    def test_company_wide_rule_applies(self, company, customer, branch, item):
        CommissionRule.objects.create(
            company=company, name="Standard", rate_percent=Decimal("2.5")
        )
        so = order(company, customer, branch, item, 10000, "SO-C1")
        assert so.commission_amount == Decimal("250.00")

    def test_min_order_value_gates_the_rule(self, company, customer, branch, item):
        CommissionRule.objects.create(
            company=company, name="Big deals", rate_percent=Decimal("5"),
            min_order_value=Decimal("50000"),
        )
        so = order(company, customer, branch, item, 10000, "SO-C2")
        assert so.commission_amount == Decimal(0)

    def test_tier_specific_rule_beats_the_catch_all(self, company, customer, branch, item):
        gold = CustomerTier.objects.create(
            company=company, name="Gold", min_annual_revenue=Decimal("1")
        )
        customer.tier = gold
        customer.save()
        CommissionRule.objects.create(company=company, name="Base", rate_percent=Decimal("2"))
        CommissionRule.objects.create(
            company=company, name="Gold", tier=gold, rate_percent=Decimal("4")
        )
        so = order(company, customer, branch, item, 10000, "SO-C3")
        assert so.commission_amount == Decimal("400.00")

    def test_inactive_rule_is_ignored(self, company, customer, branch, item):
        CommissionRule.objects.create(
            company=company, name="Old", rate_percent=Decimal("9"), is_active=False
        )
        so = order(company, customer, branch, item, 10000, "SO-C4")
        assert so.commission_amount == Decimal(0)

    def test_api_shows_the_rule_behind_the_number(self, auth_client, company, customer, branch, item):
        CommissionRule.objects.create(company=company, name="Standard", rate_percent=Decimal("2.5"))
        so = order(company, customer, branch, item, 10000, "SO-C5")
        r = auth_client.get(f"/api/selling/sales-orders/{so.pk}/commission/")
        assert r.status_code == 200
        assert r.data["amount"] == "250.00" and "Standard" in r.data["rule"]


@pytest.mark.django_db
class TestLeadScoring:
    """CRM-RULE-001."""

    @pytest.fixture
    def lead(self, company):
        return Lead.objects.create(
            company=company, lead_name="Prospect", email="p@x.com", source="Referral"
        )

    def test_no_rules_means_score_stays_zero(self, lead):
        """An unscored lead is unscored, not a bad one."""
        assert lead.recalculate_score() == 0

    def test_not_empty_rule_awards_points(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Has email", field_name="email",
            match_type="not_empty", points=30,
        )
        assert lead.recalculate_score() == 30

    def test_equals_rule_matches_a_value(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Referral", field_name="source",
            match_type="equals", match_value="referral", points=40,
        )
        assert lead.recalculate_score() == 40

    def test_rules_accumulate(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Has email", field_name="email",
            match_type="not_empty", points=30,
        )
        LeadScoringRule.objects.create(
            company=company, name="Referral", field_name="source",
            match_type="equals", match_value="Referral", points=40,
        )
        assert lead.recalculate_score() == 70

    def test_score_is_capped_at_100(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Huge", field_name="email",
            match_type="not_empty", points=500,
        )
        assert lead.recalculate_score() == 100

    def test_negative_points_cannot_go_below_zero(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Penalty", field_name="email",
            match_type="not_empty", points=-50,
        )
        assert lead.recalculate_score() == 0

    def test_unmatched_rule_awards_nothing(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Web", field_name="source",
            match_type="equals", match_value="Website", points=40,
        )
        assert lead.recalculate_score() == 0

    def test_breakdown_explains_the_score(self, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Has email", field_name="email",
            match_type="not_empty", points=30,
        )
        assert lead.score_breakdown() == [{"rule": "Has email", "points": 30}]

    def test_api_rescore(self, auth_client, company, lead):
        LeadScoringRule.objects.create(
            company=company, name="Has email", field_name="email",
            match_type="not_empty", points=30,
        )
        r = auth_client.post(f"/api/crm/leads/{lead.pk}/rescore/")
        assert r.status_code == 200 and r.data["score"] == 30


@pytest.mark.django_db
class TestSupplierScorecard:
    """PRC-CTRL-003."""

    @pytest.fixture
    def supplier(self, company):
        return Supplier.objects.create(company=company, name="Vendor")

    @pytest.fixture
    def criteria(self, company):
        return (
            SupplierScorecardCriterion.objects.create(
                company=company, name="Quality", weight=Decimal("60"), max_score=5
            ),
            SupplierScorecardCriterion.objects.create(
                company=company, name="Timeliness", weight=Decimal("40"), max_score=5
            ),
        )

    def card(self, supplier):
        return SupplierScorecard.objects.create(
            supplier=supplier, period_start=date(2026, 1, 1), period_end=date(2026, 3, 31)
        )

    def test_unscored_card_has_no_score(self, supplier):
        """Not zero — unscored and zero are different things."""
        assert self.card(supplier).weighted_score is None

    def test_weighted_score(self, supplier, criteria):
        quality, timeliness = criteria
        c = self.card(supplier)
        SupplierScore.objects.create(scorecard=c, criterion=quality, score=Decimal("5"))
        SupplierScore.objects.create(scorecard=c, criterion=timeliness, score=Decimal("2.5"))
        # (5/5*60 + 2.5/5*40) / 100 * 100 = 80
        assert c.weighted_score == Decimal("80.00")

    def test_weights_need_not_sum_to_100(self, company, supplier):
        a = SupplierScorecardCriterion.objects.create(
            company=company, name="A", weight=Decimal("3"), max_score=10
        )
        b = SupplierScorecardCriterion.objects.create(
            company=company, name="B", weight=Decimal("1"), max_score=10
        )
        c = self.card(supplier)
        SupplierScore.objects.create(scorecard=c, criterion=a, score=Decimal("10"))
        SupplierScore.objects.create(scorecard=c, criterion=b, score=Decimal("0"))
        assert c.weighted_score == Decimal("75.00")

    def test_score_above_the_maximum_rejected(self, supplier, criteria):
        quality, _ = criteria
        c = self.card(supplier)
        with pytest.raises(ValidationError, match="between 0 and 5"):
            SupplierScore.objects.create(scorecard=c, criterion=quality, score=Decimal("9"))

    def test_changing_weights_changes_the_score(self, supplier, criteria):
        """Proof the score comes from Procurement's weights, not from code."""
        quality, timeliness = criteria
        c = self.card(supplier)
        SupplierScore.objects.create(scorecard=c, criterion=quality, score=Decimal("5"))
        SupplierScore.objects.create(scorecard=c, criterion=timeliness, score=Decimal("0"))
        assert c.weighted_score == Decimal("60.00")
        quality.weight = Decimal("90")
        quality.save()
        # Weights are normalised by their total, so quality is now 90 of 130:
        # full marks on it alone earns 69.23%, not 90%.
        assert c.weighted_score == Decimal("69.23")


@pytest.mark.django_db
class TestLatePenalty:
    """PRC-RULE-003."""

    @pytest.fixture
    def supplier(self, company):
        return Supplier.objects.create(company=company, name="Vendor")

    def po(self, company, supplier, branch, item, days_late, number):
        p = PurchaseOrder.objects.create(
            company=company, supplier=supplier, branch=branch, po_number=number,
            transaction_date=date.today(), status="Submitted",
            required_by=date.today() - timedelta(days=days_late),
        )
        PurchaseOrderItem.objects.create(purchase_order=p, item=item, qty=1, rate=10000)
        p.recalculate_totals()
        p.refresh_from_db()
        return p

    def test_no_terms_means_no_penalty(self, company, supplier, branch, item):
        """Silence in a contract means no penalty, not a default one."""
        p = self.po(company, supplier, branch, item, 30, "PO-L0")
        assert p.late_penalty() == Decimal(0)

    def test_company_default_term_applies(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(company=company, percent_per_day=Decimal("0.5"))
        p = self.po(company, supplier, branch, item, 10, "PO-L1")
        assert p.late_penalty() == Decimal("500.00")  # 10d * 0.5% * 10000

    def test_grace_days_are_free(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(
            company=company, percent_per_day=Decimal("0.5"), grace_days=5
        )
        p = self.po(company, supplier, branch, item, 10, "PO-L2")
        assert p.late_penalty() == Decimal("250.00")  # only 5 chargeable days

    def test_within_grace_no_penalty(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(
            company=company, percent_per_day=Decimal("0.5"), grace_days=15
        )
        p = self.po(company, supplier, branch, item, 10, "PO-L3")
        assert p.late_penalty() == Decimal(0)

    def test_cap_is_honoured(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(
            company=company, percent_per_day=Decimal("1"), max_percent=Decimal("10")
        )
        p = self.po(company, supplier, branch, item, 90, "PO-L4")
        assert p.late_penalty() == Decimal("1000.00")  # capped at 10%

    def test_supplier_term_overrides_the_default(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(company=company, percent_per_day=Decimal("1"))
        LatePenaltyTerm.objects.create(
            company=company, supplier=supplier, percent_per_day=Decimal("0.1")
        )
        p = self.po(company, supplier, branch, item, 10, "PO-L5")
        assert p.late_penalty() == Decimal("100.00")

    def test_on_time_delivery_has_no_penalty(self, company, supplier, branch, item):
        LatePenaltyTerm.objects.create(company=company, percent_per_day=Decimal("1"))
        p = self.po(company, supplier, branch, item, -5, "PO-L6")  # due in future
        assert p.late_penalty() == Decimal(0)
