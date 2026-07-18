"""Tests for the HR-configurable policy layer: HR-RULE-001 (leave accrual),
HR-RULE-003 (end of service), and the de-hardcoding of HR-RULE-002/004.

The spec gives no rates for these because they are HR's to set. Nothing here
asserts a statutory number — every figure in these tests is one the test itself
configured, exactly as HR would.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.hr.models import (
    Department,
    Employee,
    EndOfServiceBand,
    EndOfServicePolicy,
    HRPolicy,
    LeaveEntitlement,
    LeaveRequest,
    Payroll,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Cfg Co", code="CFG-CO")


@pytest.fixture
def auth_client(api_client, django_user_model, company):
    u = django_user_model.objects.create_superuser(email="cfg@x.com", password="testpass123")
    api_client.force_authenticate(u)
    return api_client


@pytest.fixture
def department(company):
    return Department.objects.create(company=company, name="Ops")


def employee(company, department, joined, eid="C-1", **kw):
    return Employee.objects.create(
        company=company, department=department, employee_id=eid,
        first_name="A", last_name="B", date_of_joining=joined, **kw
    )


def years_ago(n):
    return date.today() - timedelta(days=int(365.25 * n))


@pytest.mark.django_db
class TestDefaultsPreserveOldBehaviour:
    """An unconfigured company must behave exactly as it did when these numbers
    were constants."""

    def test_probation_still_90_days(self, company, department):
        e = employee(company, department, date(2026, 1, 1))
        assert e.probation_end_date == date(2026, 4, 1)

    def test_leave_still_21_days(self, company, department):
        assert employee(company, department, years_ago(2)).leave_entitlement_days() == Decimal(21)

    def test_overtime_still_1_5x(self, company, department):
        e = employee(company, department, years_ago(2))
        p = Payroll.objects.create(
            employee=e, pay_period_start=date(2026, 1, 1), pay_period_end=date(2026, 1, 31),
            basic_salary=Decimal("10000"), base_hourly_rate=Decimal("50"),
            overtime_weekday_hours=Decimal("10"),
        )
        assert p.overtime_amount == Decimal("750.00")

    def test_reading_a_policy_does_not_create_one(self, company, department):
        employee(company, department, years_ago(1)).policy
        assert HRPolicy.objects.count() == 0


@pytest.mark.django_db
class TestHRConfiguredNumbers:
    def test_hr_can_change_probation_length(self, company, department):
        HRPolicy.objects.create(company=company, probation_days=180)
        e = employee(company, department, date(2026, 1, 1))
        assert e.probation_end_date == date(2026, 6, 30)

    def test_hr_can_change_overtime_multipliers(self, company, department):
        HRPolicy.objects.create(
            company=company, overtime_weekday_multiplier=Decimal("1.25"),
            overtime_holiday_multiplier=Decimal("3"),
        )
        e = employee(company, department, years_ago(1))
        p = Payroll.objects.create(
            employee=e, pay_period_start=date(2026, 1, 1), pay_period_end=date(2026, 1, 31),
            basic_salary=Decimal("1"), base_hourly_rate=Decimal("100"),
            overtime_weekday_hours=Decimal("2"), overtime_holiday_hours=Decimal("1"),
        )
        assert p.overtime_amount == Decimal("550.00")  # 2*100*1.25 + 1*100*3


@pytest.mark.django_db
class TestLeaveEntitlement:
    """HR-RULE-001."""

    def test_rule_overrides_the_default(self, company, department):
        LeaveEntitlement.objects.create(company=company, days_per_year=Decimal(30))
        assert employee(company, department, years_ago(1)).leave_entitlement_days() == Decimal(30)

    def test_tenure_band_applies_once_reached(self, company, department):
        LeaveEntitlement.objects.create(company=company, min_tenure_years=0, days_per_year=Decimal(21))
        LeaveEntitlement.objects.create(company=company, min_tenure_years=5, days_per_year=Decimal(30))
        junior = employee(company, department, years_ago(2), "J-1")
        senior = employee(company, department, years_ago(7), "S-1")
        assert junior.leave_entitlement_days() == Decimal(21)
        assert senior.leave_entitlement_days() == Decimal(30)

    def test_employment_type_rule_beats_the_catch_all(self, company, department):
        LeaveEntitlement.objects.create(company=company, days_per_year=Decimal(21))
        LeaveEntitlement.objects.create(
            company=company, employment_type="Contract", days_per_year=Decimal(10)
        )
        c = employee(company, department, years_ago(1), "K-1", employment_type="Contract")
        f = employee(company, department, years_ago(1), "F-1", employment_type="Full-time")
        assert c.leave_entitlement_days() == Decimal(10)
        assert f.leave_entitlement_days() == Decimal(21)

    def test_inactive_rule_is_ignored(self, company, department):
        LeaveEntitlement.objects.create(
            company=company, days_per_year=Decimal(99), is_active=False
        )
        assert employee(company, department, years_ago(1)).leave_entitlement_days() == Decimal(21)

    def test_monthly_accrual_is_the_year_over_twelve(self, company, department):
        LeaveEntitlement.objects.create(company=company, days_per_year=Decimal(24))
        assert employee(company, department, years_ago(1)).monthly_leave_accrual() == Decimal("2.00")

    def test_balance_check_uses_the_configured_entitlement(self, company, department):
        LeaveEntitlement.objects.create(company=company, days_per_year=Decimal(5))
        e = employee(company, department, years_ago(1))
        lr = LeaveRequest.objects.create(
            employee=e, leave_type="Annual", year=2026,
            start_date=date(2026, 2, 1), end_date=date(2026, 2, 10), status="Pending",
        )
        with pytest.raises(ValidationError, match=r"5\.00 day"):
            lr.check_balance()

    def test_api_reports_entitlement(self, auth_client, company, department):
        LeaveEntitlement.objects.create(company=company, days_per_year=Decimal(30))
        e = employee(company, department, years_ago(3))
        r = auth_client.get(f"/api/hr/employees/{e.pk}/leave_entitlement/")
        assert r.status_code == 200
        assert r.data["days_per_year"] == "30.00"
        assert r.data["accrual_per_month"] == "2.50"


@pytest.mark.django_db
class TestEndOfService:
    """HR-RULE-003. Every rate below is one this test configured — the code
    contributes no statutory numbers of its own."""

    @pytest.fixture
    def policy(self, company):
        """A shape a company might enter: 0-5 yrs at half a month per year,
        5+ at a full month, resignation paying a third then two thirds."""
        p = EndOfServicePolicy.objects.create(company=company, wage_basis="basic")
        EndOfServiceBand.objects.create(
            policy=p, from_years=0, to_years=5,
            months_per_year=Decimal("0.5"), resignation_fraction=Decimal("0.333"),
        )
        EndOfServiceBand.objects.create(
            policy=p, from_years=5, to_years=None,
            months_per_year=Decimal("1"), resignation_fraction=Decimal("0.667"),
        )
        return p

    def test_no_policy_raises_rather_than_returning_zero(self, company, department):
        e = employee(company, department, years_ago(10), salary=Decimal("10000"))
        with pytest.raises(ValidationError, match="No end-of-service policy"):
            e.end_of_service_benefit()

    def test_policy_with_no_bands_also_raises(self, company, department):
        EndOfServicePolicy.objects.create(company=company)
        e = employee(company, department, years_ago(10), salary=Decimal("10000"))
        with pytest.raises(ValidationError, match="No end-of-service policy"):
            e.end_of_service_benefit()

    def test_within_the_first_band(self, company, department, policy):
        e = employee(company, department, years_ago(4), salary=Decimal("10000"))
        r = e.end_of_service_benefit()
        assert r["months_accrued"] == Decimal("2.00")   # 4 * 0.5
        assert r["amount"] == Decimal("20000.00")

    def test_spanning_both_bands(self, company, department, policy):
        e = employee(company, department, years_ago(8), salary=Decimal("10000"))
        r = e.end_of_service_benefit()
        # 5 * 0.5 + 3 * 1.0 = 5.5 months
        assert r["months_accrued"] == Decimal("5.50")
        assert r["amount"] == Decimal("55000.00")

    def test_resignation_applies_each_bands_fraction(self, company, department, policy):
        e = employee(company, department, years_ago(8), salary=Decimal("10000"))
        r = e.end_of_service_benefit(resigned=True)
        # 5*0.5*0.333 + 3*1*0.667 = 0.8325 + 2.001 = 2.83
        assert r["months_accrued"] == Decimal("2.83")
        assert r["resigned"] is True

    def test_breakdown_shows_the_working(self, company, department, policy):
        e = employee(company, department, years_ago(8), salary=Decimal("10000"))
        r = e.end_of_service_benefit()
        assert len(r["breakdown"]) == 2
        assert r["breakdown"][0]["years_counted"] == Decimal("5.00")

    def test_changing_the_bands_changes_the_answer(self, company, department, policy):
        """Proof the number comes from HR's configuration, not from the code."""
        e = employee(company, department, years_ago(4), salary=Decimal("10000"))
        assert e.end_of_service_benefit()["amount"] == Decimal("20000.00")
        band = policy.bands.first()
        band.months_per_year = Decimal("1")
        band.save()
        assert e.end_of_service_benefit()["amount"] == Decimal("40000.00")

    def test_gross_wage_basis_uses_the_latest_payroll(self, company, department, policy):
        policy.wage_basis = "gross"
        policy.save()
        e = employee(company, department, years_ago(4), salary=Decimal("10000"))
        Payroll.objects.create(
            employee=e, pay_period_start=date(2026, 1, 1), pay_period_end=date(2026, 1, 31),
            basic_salary=Decimal("10000"), housing_allowance=Decimal("2000"),
        )
        r = e.end_of_service_benefit()
        assert r["monthly_wage"] == Decimal("12000.00")

    def test_no_tenure_no_benefit(self, company, department, policy):
        e = employee(company, department, date.today(), salary=Decimal("10000"))
        assert e.end_of_service_benefit()["amount"] == Decimal("0.00")

    def test_api_returns_the_calculation(self, auth_client, company, department, policy):
        e = employee(company, department, years_ago(8), salary=Decimal("10000"))
        r = auth_client.get(f"/api/hr/employees/{e.pk}/end_of_service/")
        assert r.status_code == 200
        assert r.data["amount"] == Decimal("55000.00")

    def test_api_honours_the_resigned_flag(self, auth_client, company, department, policy):
        e = employee(company, department, years_ago(8), salary=Decimal("10000"))
        r = auth_client.get(f"/api/hr/employees/{e.pk}/end_of_service/?resigned=true")
        assert r.data["months_accrued"] == Decimal("2.83")

    def test_api_reports_the_missing_policy_plainly(self, auth_client, company, department):
        e = employee(company, department, years_ago(3), salary=Decimal("10000"))
        r = auth_client.get(f"/api/hr/employees/{e.pk}/end_of_service/")
        assert r.status_code == 400
        assert "HR must" in r.data["detail"]
