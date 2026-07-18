"""The demo seeder must produce coherent data, not merely rows.

A demo that contradicts itself is worse than none: it teaches people to
distrust the numbers.
"""
from decimal import Decimal

import pytest
from django.core.management import call_command

from apps.buying.models import PurchaseOrder
from apps.core.models import BinLocation, Branch, CompanyProfile, Warehouse
from apps.crm.models import Lead
from apps.inventory.models import Item
from apps.invoicing.models import Invoice
from apps.selling.models import Customer, SalesOrder


@pytest.fixture
def seeded(db):
    call_command("seed_erp_demo", verbosity=0)
    return CompanyProfile.objects.get(code="DEMO-KSA")


@pytest.mark.django_db
class TestSeeder:
    def test_it_is_idempotent(self, seeded):
        call_command("seed_erp_demo", verbosity=0)
        assert CompanyProfile.objects.filter(code="DEMO-KSA").count() == 1
        assert PurchaseOrder.objects.filter(po_number="PO-DEMO-0001").count() == 1
        assert Invoice.objects.filter(invoice_number="INV-DEMO-0001").count() == 1

    def test_branches_got_warehouses_and_bins(self, seeded):
        assert Branch.objects.filter(company=seeded).count() == 3
        for branch in Branch.objects.filter(company=seeded):
            wh = Warehouse.objects.get(branch=branch)
            assert BinLocation.objects.filter(warehouse=wh).count() == 2

    def test_one_head_office_only(self, seeded):
        assert Branch.objects.filter(company=seeded, branch_type="Head Office").count() == 1

    def test_stock_reconciles_across_the_document_chain(self, seeded):
        """400 opening + 195 accepted on the GRN - 50 delivered = 545 available."""
        wh = Warehouse.objects.get(branch__company=seeded, branch__code="RUH")
        steel = Item.objects.get(company=seeded, item_code="STL-100")
        assert steel.stock_in_warehouse(wh) == Decimal("595.00")
        assert steel.reserved_qty(wh) == Decimal("50.00")
        assert steel.available_qty(wh) == Decimal("545.00")

    def test_goods_receipt_recorded_the_rejection(self, seeded):
        po = PurchaseOrder.objects.get(po_number="PO-DEMO-0001")
        line = po.items.first()
        assert line.qty == Decimal("200.00")
        assert line.accepted_qty == Decimal("195.00")

    def test_three_way_match_reports_the_short_delivery(self, seeded):
        po = PurchaseOrder.objects.get(po_number="PO-DEMO-0001")
        matched, issues = po.three_way_match()
        assert matched is False and "received 195.00" in issues[0]

    def test_late_penalty_is_actually_demonstrated(self, seeded):
        """A demo where the penalty is always zero doesn't demo the penalty."""
        po = PurchaseOrder.objects.get(po_number="PO-DEMO-0001")
        assert po.late_penalty() > 0

    def test_invoice_matches_the_order_it_came_from(self, seeded):
        so = SalesOrder.objects.get(so_number="SO-DEMO-0001")
        inv = Invoice.objects.get(invoice_number="INV-DEMO-0001")
        assert inv.against_sales_order == so
        assert inv.total == so.grand_total
        assert inv.line_items.count() == so.items.count()

    def test_tiers_are_earned_not_assigned(self, seeded):
        """One customer reaches a tier on real history; the other genuinely
        doesn't — the demo shows the rule working, not a filled-in column."""
        big = Customer.objects.get(company=seeded, name__startswith="مؤسسة")
        small = Customer.objects.get(company=seeded, name="Al-Faisal Contracting")
        assert big.tier is not None
        assert small.tier is None

    def test_lead_scores_differ_by_the_configured_rules(self, seeded):
        scores = {l.lead_name: l.score for l in Lead.objects.filter(company=seeded)}
        assert scores["Khalid Al-Otaibi"] > scores["Sara Nasser"] > scores["Walk-in enquiry"]

    def test_policies_are_populated_for_every_configurable_rule(self, seeded):
        from apps.buying.models import LatePenaltyTerm, SupplierScorecardCriterion
        from apps.crm.models import LeadScoringRule
        from apps.hr.models import EndOfServicePolicy, HRPolicy, LeaveEntitlement
        from apps.selling.models import CommissionRule, CustomerTier

        assert HRPolicy.objects.filter(company=seeded).exists()
        assert LeaveEntitlement.objects.filter(company=seeded).count() == 3
        assert EndOfServicePolicy.objects.get(company=seeded).bands.count() == 2
        assert CustomerTier.objects.filter(company=seeded).count() == 3
        assert CommissionRule.objects.filter(company=seeded).count() == 2
        assert SupplierScorecardCriterion.objects.filter(company=seeded).count() == 3
        assert LatePenaltyTerm.objects.filter(company=seeded).exists()
        assert LeadScoringRule.objects.filter(company=seeded).count() == 4

    def test_warehouse_occupancy_is_real(self, seeded):
        wh = Warehouse.objects.get(branch__company=seeded, branch__code="RUH")
        assert 0 < wh.occupancy_rate < 100


@pytest.mark.django_db
class TestBulkDemoData:
    """The demo should fill the company with several purchase orders and
    customer invoices in varied states — not one of each."""

    def test_multiple_purchase_orders_across_statuses(self, seeded):
        from apps.buying.models import PurchaseOrder
        pos = PurchaseOrder.objects.filter(company=seeded)
        assert pos.count() >= 5
        statuses = set(pos.values_list("status", flat=True))
        # Both draft and submitted present — the cycle at different stages.
        assert "Draft" in statuses and "Submitted" in statuses

    def test_multiple_customer_invoices_in_varied_payment_states(self, seeded):
        from apps.invoicing.models import Invoice
        invoices = Invoice.objects.filter(company=seeded, invoice_type="sales")
        assert invoices.count() >= 5
        # A paid, a part-paid and an unpaid invoice all exist, so receivables
        # and aging screens show something real rather than all-identical rows.
        fully_paid = any(i.paid_amount and i.paid_amount >= i.total for i in invoices)
        part_paid = any(i.paid_amount and 0 < i.paid_amount < i.total for i in invoices)
        unpaid = any(not i.paid_amount for i in invoices)
        assert fully_paid and part_paid and unpaid

    def test_purchase_orders_span_multiple_branches(self, seeded):
        from apps.buying.models import PurchaseOrder
        branches = set(
            PurchaseOrder.objects.filter(company=seeded).values_list("branch__code", flat=True)
        )
        assert len(branches) >= 2
