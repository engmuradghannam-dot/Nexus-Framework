"""Tests for Payroll.post_to_ledger() (apps.hr) and the Attendance/Timesheet
Employee FK relations (apps.attendance).

Previously Payroll had a full allowance/deduction breakdown and a "Paid"
status but never actually posted the salary expense anywhere -- despite
apps.accounts.JournalEntry/Account already existing and Invoice already
doing exactly this. Attendance/Timesheet also only stored employee_name as
free text, with no real link back to hr.Employee.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Account
from apps.attendance.models import Attendance, Timesheet
from apps.core.models import CompanyProfile
from apps.hr.models import Employee, Payroll


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="payroll-ledger@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Payroll Ledger Co", code="PL-CO")


@pytest.fixture
def employee(company):
    return Employee.objects.create(
        company=company, employee_id="EMP-PL-1", first_name="Nora", last_name="Saleh",
    )


@pytest.fixture
def coa(company):
    nums = {"5200": ("Salaries", "Expense"), "1200": ("Bank", "Asset"), "2100": ("A/P", "Liability")}
    return {n: Account.objects.create(company=company, account_number=n, account_name=nm,
                                      account_type=r, root_type=r) for n, (nm, r) in nums.items()}


@pytest.fixture
def payroll(employee):
    return Payroll.objects.create(
        employee=employee, pay_period_start=date(2026, 1, 1), pay_period_end=date(2026, 1, 31),
        basic_salary=5000, housing_allowance=1000, social_insurance=300, tax=200,
        status="Paid", payment_date=date(2026, 2, 1),
    )


@pytest.mark.django_db
class TestPayrollPostToLedger:
    def test_posts_balanced_entries_split_by_net_and_deductions(self, payroll, coa):
        assert payroll.gross_salary == Decimal("6000")
        assert payroll.total_deductions == Decimal("500")
        assert payroll.net_salary == Decimal("5500")

        ok, msg = payroll.post_to_ledger()
        assert ok, msg
        payroll.refresh_from_db()
        assert payroll.posted_to_ledger is True

        expense = Account.objects.get(pk=coa["5200"].pk)
        bank = Account.objects.get(pk=coa["1200"].pk)
        payable = Account.objects.get(pk=coa["2100"].pk)
        assert expense.balance == Decimal("6000")
        assert bank.balance == Decimal("-5500")
        assert payable.balance == Decimal("500")  # liability: credit increases it

    def test_cannot_post_twice(self, payroll, coa):
        payroll.post_to_ledger()
        ok, msg = payroll.post_to_ledger()
        assert not ok and "مسبقاً" in msg

    def test_cannot_post_unless_paid(self, employee, coa):
        p = Payroll.objects.create(
            employee=employee, pay_period_start=date(2026, 1, 1), pay_period_end=date(2026, 1, 31),
            basic_salary=1000, status="Draft",
        )
        ok, msg = p.post_to_ledger()
        assert not ok

    def test_fails_gracefully_without_chart_of_accounts(self, payroll):
        ok, msg = payroll.post_to_ledger()
        assert not ok and "seed_accounting" in msg

    def test_no_deduction_leg_when_fully_gross_is_net(self, employee, coa):
        p = Payroll.objects.create(
            employee=employee, pay_period_start=date(2026, 2, 1), pay_period_end=date(2026, 2, 28),
            basic_salary=1000, status="Paid",
        )
        ok, msg = p.post_to_ledger()
        assert ok, msg
        assert Account.objects.get(pk=coa["5200"].pk).balance == Decimal("1000")
        assert Account.objects.get(pk=coa["1200"].pk).balance == Decimal("-1000")
        assert Account.objects.get(pk=coa["2100"].pk).balance == Decimal("0")

    def test_status_transition_via_api_triggers_posting(self, auth_client, employee, coa):
        p = Payroll.objects.create(
            employee=employee, pay_period_start=date(2026, 3, 1), pay_period_end=date(2026, 3, 31),
            basic_salary=2000, status="Draft",
        )
        r1 = auth_client.patch(f"/api/hr/payrolls/{p.pk}/", {"status": "Approved"})
        assert r1.status_code == 200, r1.data
        response = auth_client.patch(f"/api/hr/payrolls/{p.pk}/", {"status": "Paid"})
        assert response.status_code == 200, response.data
        p.refresh_from_db()
        assert p.posted_to_ledger is True


@pytest.mark.django_db
class TestAttendanceTimesheetEmployeeLink:
    def test_attendance_links_to_employee(self, employee):
        att = Attendance.objects.create(
            employee=employee, employee_name="Nora Saleh", date=date(2026, 1, 5),
        )
        assert att.employee == employee

    def test_timesheet_links_to_employee_and_project(self, employee):
        from apps.pmo.models import Project, Task

        project = Project.objects.create(name="Timesheet Project")
        task = Task.objects.create(project=project, title="Do the thing")
        ts = Timesheet.objects.create(
            employee=employee, employee_name="Nora Saleh", date=date(2026, 1, 5),
            project_link=project, task_link=task, hours=4,
        )
        assert ts.employee == employee
        assert ts.project_link == project
        assert ts.task_link == task
