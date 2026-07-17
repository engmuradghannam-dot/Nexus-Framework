"""Tests for the HR rules from ERP_Complete_System.xlsx.

Covers HR-RULE-002 (probation period) and HR-RULE-004 (overtime rates).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.models import CompanyProfile
from apps.hr.models import Department, Employee, Payroll


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="HR Co", code="HR-CO")


@pytest.fixture
def department(company):
    return Department.objects.create(company=company, name="Ops")


def make_employee(company, department, joined, **kw):
    return Employee.objects.create(
        company=company, department=department,
        employee_id=kw.pop("employee_id", f"E-{joined}"),
        first_name="Test", last_name="Person", date_of_joining=joined, **kw
    )


@pytest.mark.django_db
class TestProbation:
    """HR-RULE-002: hire date + 90 days."""

    def test_probation_ends_90_days_after_hire(self, company, department):
        e = make_employee(company, department, date(2026, 1, 1))
        assert e.probation_end_date == date(2026, 4, 1)

    def test_review_flagged_once_the_window_closes(self, company, department):
        e = make_employee(company, department, date.today() - timedelta(days=91))
        assert e.probation_review_due is True

    def test_not_flagged_before_the_window_closes(self, company, department):
        e = make_employee(company, department, date.today() - timedelta(days=30))
        assert e.probation_review_due is False
        assert e.days_to_probation_end == 60

    def test_flag_clears_once_reviewed(self, company, department):
        e = make_employee(company, department, date.today() - timedelta(days=120))
        assert e.probation_review_due is True
        e.probation_reviewed_at = date.today()
        e.save()
        assert e.probation_review_due is False

    def test_flagged_exactly_on_the_ninetieth_day(self, company, department):
        e = make_employee(company, department, date.today() - timedelta(days=90))
        assert e.probation_review_due is True

    def test_no_hire_date_means_no_flag(self, company, department):
        e = Employee.objects.create(
            company=company, department=department, employee_id="E-NONE",
            first_name="No", last_name="Date",
        )
        assert e.probation_end_date is None
        assert e.probation_review_due is False

    def test_inactive_employees_are_not_flagged(self, company, department):
        e = make_employee(
            company, department, date.today() - timedelta(days=200), status="Resigned"
        )
        assert e.probation_review_due is False


@pytest.mark.django_db
class TestOvertimeRates:
    """HR-RULE-004: 1.5x weekday, 2x weekend/holiday."""

    @pytest.fixture
    def employee(self, company, department):
        return make_employee(company, department, date(2025, 1, 1), employee_id="OT-1")

    def payroll(self, employee, **kw):
        return Payroll.objects.create(
            employee=employee, pay_period_start=date(2026, 1, 1),
            pay_period_end=date(2026, 1, 31), basic_salary=Decimal("10000"), **kw
        )

    def test_weekday_overtime_at_1_5x(self, employee):
        p = self.payroll(
            employee, base_hourly_rate=Decimal("50"), overtime_weekday_hours=Decimal("10")
        )
        assert p.overtime_amount == Decimal("750.00")  # 10 * 50 * 1.5

    def test_holiday_overtime_at_2x(self, employee):
        p = self.payroll(
            employee, base_hourly_rate=Decimal("50"), overtime_holiday_hours=Decimal("10")
        )
        assert p.overtime_amount == Decimal("1000.00")  # 10 * 50 * 2

    def test_both_buckets_sum(self, employee):
        p = self.payroll(
            employee, base_hourly_rate=Decimal("50"),
            overtime_weekday_hours=Decimal("8"), overtime_holiday_hours=Decimal("4"),
        )
        assert p.overtime_amount == Decimal("1000.00")  # 600 + 400

    def test_legacy_flat_rate_is_untouched(self, employee):
        """Existing rows must not silently gain a 1.5x multiplier — it was never
        defined whether overtime_rate was the ordinary or the overtime wage."""
        p = self.payroll(
            employee, overtime_hours=Decimal("10"), overtime_rate=Decimal("75")
        )
        assert p.overtime_amount == Decimal("750.00")  # flat, no multiplier

    def test_legacy_and_new_can_coexist(self, employee):
        p = self.payroll(
            employee, overtime_hours=Decimal("2"), overtime_rate=Decimal("100"),
            base_hourly_rate=Decimal("50"), overtime_weekday_hours=Decimal("4"),
        )
        assert p.overtime_amount == Decimal("500.00")  # 200 legacy + 300 weekday

    def test_no_overtime_is_zero(self, employee):
        assert self.payroll(employee).overtime_amount == Decimal("0.00")

    def test_overtime_reaches_gross_salary(self, employee):
        p = self.payroll(
            employee, base_hourly_rate=Decimal("50"), overtime_weekday_hours=Decimal("10")
        )
        assert p.gross_salary == Decimal("10750.00")
