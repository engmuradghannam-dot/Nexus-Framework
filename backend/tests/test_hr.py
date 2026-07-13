"""Pytest tests for the HR module (apps.hr): payroll computation and
annual-leave balance tracking — both directly affect what employees get
paid and had no test coverage (P1 #4 follow-up).
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.hr.models import Employee, LeaveRequest, Payroll


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="hr@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="HR Co", code="HR-CO")


@pytest.fixture
def employee(company):
    return Employee.objects.create(
        company=company, employee_id="EMP-001", first_name="Sara", last_name="Ahmed",
    )


@pytest.mark.django_db
class TestPayrollComputation:
    def test_gross_salary_sums_pay_components(self, employee):
        p = Payroll.objects.create(
            employee=employee,
            pay_period_start=date(2026, 1, 1),
            pay_period_end=date(2026, 1, 31),
            basic_salary=5000,
            housing_allowance=1000,
            transport_allowance=500,
            food_allowance=200,
            other_allowances=100,
            overtime_hours=10,
            overtime_rate=25,
            bonuses=300,
        )
        # overtime_amount = 10*25=250; gross = 5000+1000+500+200+100+250+300 = 7350
        assert p.overtime_amount == Decimal("250")
        assert p.gross_salary == Decimal("7350")

    def test_net_salary_subtracts_all_deductions(self, employee):
        p = Payroll.objects.create(
            employee=employee,
            pay_period_start=date(2026, 1, 1),
            pay_period_end=date(2026, 1, 31),
            basic_salary=5000,
            social_insurance=450,
            health_insurance=100,
            loan_deductions=200,
            advance_payments=50,
            deductions=25,
            tax=75,
        )
        # gross = 5000; deductions total = 450+100+200+50+25+75 = 900
        assert p.total_deductions == Decimal("900")
        assert p.net_salary == Decimal("4100")

    def test_zero_overtime_does_not_error(self, employee):
        p = Payroll.objects.create(
            employee=employee,
            pay_period_start=date(2026, 1, 1),
            pay_period_end=date(2026, 1, 31),
            basic_salary=3000,
        )
        assert p.overtime_amount == 0
        assert p.net_salary == Decimal("3000")


@pytest.mark.django_db
class TestLeaveBalance:
    def test_duration_days_is_inclusive(self, employee):
        lr = LeaveRequest.objects.create(
            employee=employee, leave_type="Annual",
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 5),
        )
        assert lr.duration_days == 5

    def test_year_defaults_from_start_date(self, employee):
        lr = LeaveRequest.objects.create(
            employee=employee, leave_type="Annual",
            start_date=date(2026, 6, 10), end_date=date(2026, 6, 12),
        )
        assert lr.year == 2026

    def test_remaining_balance_deducts_approved_annual_leave(self, employee):
        LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2026, status="Approved",
            start_date=date(2026, 1, 5), end_date=date(2026, 1, 9),  # 5 days
        )
        current = LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2026, status="Approved",
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 3),  # 3 days
        )
        # 21 - (5 already taken + 3 this request) = 13
        assert current.remaining_balance == 13

    def test_pending_leave_does_not_reduce_balance_yet(self, employee):
        LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2026, status="Approved",
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 5),  # 5 days
        )
        pending = LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2026, status="Pending",
            start_date=date(2026, 5, 1), end_date=date(2026, 5, 10),
        )
        # Only the 5 approved days count; the pending request's own days
        # aren't deducted until it's approved.
        assert pending.remaining_balance == 16

    def test_non_annual_leave_has_no_balance(self, employee):
        lr = LeaveRequest.objects.create(
            employee=employee, leave_type="Sick", year=2026,
            start_date=date(2026, 2, 1), end_date=date(2026, 2, 2),
        )
        assert lr.remaining_balance is None


@pytest.mark.django_db
class TestHRAPI:
    def test_create_employee(self, auth_client, company):
        response = auth_client.post(
            "/api/hr/employees/",
            {"company": str(company.id), "employee_id": "EMP-100", "first_name": "Omar", "last_name": "Khaled"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_leave_request(self, auth_client, employee):
        response = auth_client.post(
            "/api/hr/leave-requests/",
            {
                "employee": employee.id, "leave_type": "Annual",
                "start_date": "2026-07-01", "end_date": "2026-07-03",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/hr/employees/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
