"""Tests for FIN-RULE-004 (account validity), MFG-CTRL-005 (machine
maintenance) and CRM-CTRL-005 (consent tracking) from ERP_Complete_System.xlsx.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Account, JournalEntry
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.manufacturing.models import BOM, BOMItem, MaintenanceLog, WorkOrder, Workstation
from apps.selling.models import ConsentLog, Customer


@pytest.fixture
def alpha():
    return CompanyProfile.objects.create(name="Alpha", code="ALPHA-CO")


@pytest.fixture
def beta():
    return CompanyProfile.objects.create(name="Beta", code="BETA-CO")


def account(company, number, name, kind):
    return Account.objects.create(
        company=company, account_number=number, account_name=name, account_type=kind
    )


@pytest.mark.django_db
class TestAccountValidity:
    """FIN-RULE-004. The FK proves the account exists; it does not prove it's
    yours."""

    def test_own_accounts_pass(self, alpha):
        je = JournalEntry.objects.create(
            company=alpha, entry_number="JE-V1", posting_date=date.today(),
            debit_account=account(alpha, "1000", "Cash", "Asset"),
            credit_account=account(alpha, "4000", "Rev", "Revenue"),
            amount=Decimal("100"), total_debit=Decimal("100"), total_credit=Decimal("100"),
        )
        je.check_accounts()

    def test_another_companys_account_is_rejected(self, alpha, beta):
        je = JournalEntry.objects.create(
            company=alpha, entry_number="JE-V2", posting_date=date.today(),
            debit_account=account(alpha, "1000", "Cash", "Asset"),
            credit_account=account(beta, "4000", "Rev B", "Revenue"),
            amount=Decimal("100"), total_debit=Decimal("100"), total_credit=Decimal("100"),
        )
        with pytest.raises(ValidationError, match="belongs to"):
            je.check_accounts()

    def test_posting_is_blocked_not_just_flagged(self, alpha, beta):
        je = JournalEntry.objects.create(
            company=alpha, entry_number="JE-V3", posting_date=date.today(),
            debit_account=account(alpha, "1000", "Cash", "Asset"),
            credit_account=account(beta, "4000", "Rev B", "Revenue"),
            amount=Decimal("100"), total_debit=Decimal("100"), total_credit=Decimal("100"),
        )
        with pytest.raises(ValidationError):
            je.post_to_ledger()

    def test_same_account_both_sides_rejected(self, alpha):
        cash = account(alpha, "1000", "Cash", "Asset")
        je = JournalEntry.objects.create(
            company=alpha, entry_number="JE-V4", posting_date=date.today(),
            debit_account=cash, credit_account=cash,
            amount=Decimal("100"), total_debit=Decimal("100"), total_credit=Decimal("100"),
        )
        with pytest.raises(ValidationError, match="same account"):
            je.check_accounts()


@pytest.mark.django_db
class TestMachineMaintenance:
    """MFG-CTRL-005."""

    @pytest.fixture
    def setup(self, alpha):
        branch = Branch.objects.create(company=alpha, name="Plant", code="MC-P", address="Riyadh")
        wh = Warehouse.objects.get(branch=branch)
        rm = Item.objects.create(company=alpha, item_code="RM-M", item_name="Steel")
        fg = Item.objects.create(company=alpha, item_code="FG-M", item_name="Part")
        StockEntry.objects.create(
            company=alpha, warehouse=wh, item=rm, entry_type="Receipt", quantity=100, rate=1
        )
        bom = BOM.objects.create(company=alpha, item=fg, bom_name="B", quantity=1)
        BOMItem.objects.create(bom=bom, item=rm, qty=1, rate=1)
        return branch, wh, bom, fg

    def station(self, alpha, branch, interval, last):
        return Workstation.objects.create(
            company=alpha, branch=branch, name="Press", code="PRESS-1",
            maintenance_interval_days=interval, last_maintenance_date=last,
        )

    def work_order(self, alpha, branch, wh, bom, fg, station, number="WO-M1"):
        return WorkOrder.objects.create(
            company=alpha, branch=branch, warehouse=wh, bom=bom, wo_number=number,
            order_date=date.today(), item_to_manufacture=fg, qty_to_produce=10,
            status="Draft", workstation_ref=station,
        )

    def test_serviced_machine_releases(self, alpha, setup):
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 30, date.today() - timedelta(days=5))
        assert st.maintenance_overdue is False
        wo = self.work_order(alpha, branch, wh, bom, fg, st)
        ok, _ = wo.release(ignore_bom_approval=True)
        assert ok

    def test_overdue_machine_blocks_release(self, alpha, setup):
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 30, date.today() - timedelta(days=60))
        assert st.maintenance_overdue is True
        wo = self.work_order(alpha, branch, wh, bom, fg, st, "WO-M2")
        with pytest.raises(ValidationError, match="overdue for"):
            wo.release(ignore_bom_approval=True)

    def test_never_serviced_machine_with_a_schedule_is_overdue(self, alpha, setup):
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 30, None)
        assert st.maintenance_overdue is True

    def test_station_without_a_schedule_is_never_overdue(self, alpha, setup):
        """Otherwise this rule halts every existing shop floor on day one."""
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 0, None)
        assert st.maintenance_overdue is False
        wo = self.work_order(alpha, branch, wh, bom, fg, st, "WO-M3")
        ok, _ = wo.release(ignore_bom_approval=True)
        assert ok

    def test_work_order_without_a_station_is_unaffected(self, alpha, setup):
        branch, wh, bom, fg = setup
        wo = self.work_order(alpha, branch, wh, bom, fg, None, "WO-M4")
        ok, _ = wo.release(ignore_bom_approval=True)
        assert ok

    def test_recording_maintenance_clears_the_block_and_logs_it(self, alpha, setup):
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 30, date.today() - timedelta(days=60))
        st.record_maintenance()
        st.refresh_from_db()
        assert st.maintenance_overdue is False
        assert MaintenanceLog.objects.filter(workstation=st).count() == 1

    def test_next_due_date(self, alpha, setup):
        branch, wh, bom, fg = setup
        st = self.station(alpha, branch, 30, date(2026, 1, 1))
        assert st.next_maintenance_due == date(2026, 1, 31)


@pytest.mark.django_db
class TestConsentTracking:
    """CRM-CTRL-005."""

    @pytest.fixture
    def customer(self, alpha):
        return Customer.objects.create(company=alpha, name="Acme")

    def test_consent_defaults_to_false(self, customer):
        """Consent that was never given cannot be assumed."""
        assert customer.marketing_consent is False
        assert customer.has_consent("marketing") is False

    def test_granting_records_when(self, customer):
        customer.grant_consent("marketing")
        customer.refresh_from_db()
        assert customer.marketing_consent is True
        assert customer.marketing_consent_at is not None

    def test_withdrawal_clears_the_flag(self, customer):
        customer.grant_consent("marketing")
        customer.withdraw_consent("marketing")
        customer.refresh_from_db()
        assert customer.marketing_consent is False
        assert customer.marketing_consent_at is None

    def test_history_survives_withdrawal(self, customer):
        """A mutable flag can't prove compliance; the trail can."""
        customer.grant_consent("marketing")
        customer.withdraw_consent("marketing")
        logs = list(ConsentLog.objects.filter(customer=customer).order_by("id"))
        assert [l.granted for l in logs] == [True, False]

    def test_consent_types_are_independent(self, customer):
        customer.grant_consent("data_processing")
        assert customer.has_consent("data_processing") is True
        assert customer.has_consent("marketing") is False

    def test_unknown_consent_type_rejected(self, customer):
        with pytest.raises(ValidationError, match="Unknown consent"):
            customer.grant_consent("astrology")

    def test_actor_is_recorded(self, customer, django_user_model):
        u = django_user_model.objects.create_user(email="dpo@x.com", password="testpass123")
        customer.grant_consent("marketing", actor=u)
        assert ConsentLog.objects.get(customer=customer).actor == u
