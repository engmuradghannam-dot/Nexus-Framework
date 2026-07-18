"""Tests for BRN-CTRL-004 (monthly P&L per branch) and PRJ-CTRL-005 (change
request approval) from ERP_Complete_System.xlsx.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Account, JournalEntry
from apps.core.models import Branch, CompanyProfile
from apps.pmo.models import ChangeRequest, Project


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="PL Co", code="PL-CO")


@pytest.fixture
def riyadh(company):
    return Branch.objects.create(company=company, name="Riyadh", code="PL-R", address="Riyadh")


@pytest.fixture
def jeddah(company):
    return Branch.objects.create(company=company, name="Jeddah", code="PL-J", address="Jeddah")


@pytest.fixture
def accounts(company):
    return {
        "cash": Account.objects.create(
            company=company, account_number="1000", account_name="Cash", account_type="Asset"
        ),
        "revenue": Account.objects.create(
            company=company, account_number="4000", account_name="Sales", account_type="Income"
        ),
        "expense": Account.objects.create(
            company=company, account_number="5000", account_name="Rent", account_type="Expense"
        ),
    }


def je(company, branch, dr, cr, amount, number, when=date(2026, 3, 15)):
    return JournalEntry.objects.create(
        company=company, branch=branch, entry_number=number, posting_date=when,
        debit_account=dr, credit_account=cr, amount=Decimal(amount),
        total_debit=Decimal(amount), total_credit=Decimal(amount),
    )


PERIOD = (date(2026, 3, 1), date(2026, 3, 31))


@pytest.mark.django_db
class TestBranchProfitAndLoss:
    """BRN-CTRL-004. JournalEntry.branch existed but nothing populated it, so
    a per-branch P&L would have reported zero for every branch forever."""

    def test_income_and_expense_net_to_profit(self, company, riyadh, accounts):
        je(company, riyadh, accounts["cash"], accounts["revenue"], 10000, "JE-P1")
        je(company, riyadh, accounts["expense"], accounts["cash"], 3000, "JE-P2")
        pl = riyadh.profit_and_loss(*PERIOD)
        assert pl["income"] == Decimal("10000")
        assert pl["expense"] == Decimal("3000")
        assert pl["net_profit"] == Decimal("7000")

    def test_branches_are_separated(self, company, riyadh, jeddah, accounts):
        je(company, riyadh, accounts["cash"], accounts["revenue"], 10000, "JE-P3")
        je(company, jeddah, accounts["cash"], accounts["revenue"], 500, "JE-P4")
        assert riyadh.profit_and_loss(*PERIOD)["income"] == Decimal("10000")
        assert jeddah.profit_and_loss(*PERIOD)["income"] == Decimal("500")

    def test_entries_outside_the_period_are_excluded(self, company, riyadh, accounts):
        je(company, riyadh, accounts["cash"], accounts["revenue"], 10000, "JE-P5",
           when=date(2026, 1, 5))
        assert riyadh.profit_and_loss(*PERIOD)["income"] == Decimal(0)

    def test_untagged_entries_are_excluded_not_spread(self, company, riyadh, accounts):
        """Inventing an allocation would be worse than showing only what is
        actually attributable."""
        je(company, None, accounts["cash"], accounts["revenue"], 9999, "JE-P6")
        assert riyadh.profit_and_loss(*PERIOD)["income"] == Decimal(0)

    def test_cancelled_entries_are_excluded(self, company, riyadh, accounts):
        e = je(company, riyadh, accounts["cash"], accounts["revenue"], 10000, "JE-P7")
        e.status = "Cancelled"
        e.save()
        assert riyadh.profit_and_loss(*PERIOD)["income"] == Decimal(0)

    def test_a_loss_is_reported_as_negative(self, company, riyadh, accounts):
        je(company, riyadh, accounts["expense"], accounts["cash"], 4000, "JE-P8")
        assert riyadh.profit_and_loss(*PERIOD)["net_profit"] == Decimal("-4000")

    def test_quiet_branch_reports_zero_not_error(self, riyadh):
        pl = riyadh.profit_and_loss(*PERIOD)
        assert pl["net_profit"] == Decimal(0) and pl["entries"] == 0

    def test_payroll_posting_tags_the_branch(self, company, riyadh):
        """The tag has to actually get written, or the report is decorative."""
        from apps.hr.models import Department, Employee, Payroll

        for number, name, kind in [
            ("5200", "Salaries", "Expense"), ("1200", "Bank", "Asset"),
            ("2100", "AP", "Liability"),
        ]:
            Account.objects.get_or_create(
                company=company, account_number=number,
                defaults={"account_name": name, "account_type": kind},
            )
        dept = Department.objects.create(company=company, name="Ops")
        emp = Employee.objects.create(
            company=company, department=dept, branch=riyadh, employee_id="PL-1",
            first_name="A", last_name="B", date_of_joining=date(2025, 1, 1),
        )
        pay = Payroll.objects.create(
            employee=emp, pay_period_start=date(2026, 3, 1), pay_period_end=date(2026, 3, 31),
            basic_salary=Decimal("5000"), status="Paid", payment_date=date(2026, 3, 28),
        )
        pay.post_to_ledger()
        assert JournalEntry.objects.filter(branch=riyadh).exists()
        assert riyadh.profit_and_loss(*PERIOD)["expense"] > 0


@pytest.mark.django_db
class TestChangeRequests:
    """PRJ-CTRL-005."""

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="Tower", code="TWR", status="Active",
            budget=Decimal("100000"), end_date=date(2026, 12, 31),
        )

    @pytest.fixture
    def requester(self, django_user_model):
        return django_user_model.objects.create_user(email="pm@x.com", password="testpass123")

    @pytest.fixture
    def sponsor(self, django_user_model):
        return django_user_model.objects.create_user(email="sponsor@x.com", password="testpass123")

    def cr(self, project, requester, **kw):
        return ChangeRequest.objects.create(
            project=project, title=kw.pop("title", "Extra floor"),
            justification=kw.pop("justification", "Client asked"),
            requested_by=requester, **kw
        )

    def test_approval_applies_the_budget_change(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("25000"))
        c.submit()
        c.approve(sponsor)
        project.refresh_from_db()
        assert project.budget == Decimal("125000")

    def test_approval_applies_the_date_change(self, project, requester, sponsor):
        c = self.cr(project, requester, end_date_delta_days=30)
        c.submit()
        c.approve(sponsor)
        project.refresh_from_db()
        assert project.end_date == date(2027, 1, 30)

    def test_negative_delta_reduces_the_budget(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("-10000"))
        c.submit()
        c.approve(sponsor)
        project.refresh_from_db()
        assert project.budget == Decimal("90000")

    def test_requester_cannot_approve_their_own(self, project, requester):
        c = self.cr(project, requester, budget_delta=Decimal("25000"))
        c.submit()
        with pytest.raises(ValidationError, match="cannot approve their own"):
            c.approve(requester)

    def test_unsubmitted_request_cannot_be_approved(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("25000"))
        with pytest.raises(ValidationError, match="Only a submitted"):
            c.approve(sponsor)

    def test_submission_needs_a_justification(self, project, requester):
        c = self.cr(project, requester, justification="", budget_delta=Decimal("100"))
        with pytest.raises(ValidationError, match="justification"):
            c.submit()

    def test_a_change_that_changes_nothing_is_rejected(self, project, requester):
        c = self.cr(project, requester)
        with pytest.raises(ValidationError, match="actually change something"):
            c.submit()

    def test_rejection_leaves_the_project_alone(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("25000"))
        c.submit()
        c.reject(sponsor)
        project.refresh_from_db()
        assert project.budget == Decimal("100000")
        assert c.status == "Rejected" and c.decided_at is not None

    def test_cannot_approve_twice(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("1000"))
        c.submit()
        c.approve(sponsor)
        with pytest.raises(ValidationError, match="Only a submitted"):
            c.approve(sponsor)

    def test_the_trail_records_who_decided(self, project, requester, sponsor):
        c = self.cr(project, requester, budget_delta=Decimal("1000"))
        c.submit()
        c.approve(sponsor)
        assert c.approved_by == sponsor and c.requested_by == requester
