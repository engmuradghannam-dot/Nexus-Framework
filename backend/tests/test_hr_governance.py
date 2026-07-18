"""Tests for HR-CTRL-001 (salary confidentiality), HR-CTRL-002 (hiring
approval) and HR-CTRL-004 (termination audit) from ERP_Complete_System.xlsx.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.hr.models import Department, Employee, EmployeeTermination, Payroll
from apps.rbac.models import Role, RoleAssignment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Gov HR", code="GHR-CO")


@pytest.fixture
def department(company):
    return Department.objects.create(company=company, name="Ops")


def user_with_role(django_user_model, email, role_name=None, company=None):
    """Company access is separate from RBAC role: CompanyScopedMixin scopes on
    managed_companies (the reverse of CompanyProfile.super_admin), so a viewer
    needs that too or the record is simply 404 and nothing about salary
    visibility is exercised."""
    u = django_user_model.objects.create_user(email=email, password="testpass123")
    if role_name:
        RoleAssignment.objects.create(
            user=u,
            role=Role.objects.get_or_create(name=role_name, defaults={"permissions": {}})[0],
        )
    if company is not None:
        company.super_admin = u
        company.save(update_fields=["super_admin"])
    return u


def make_employee(company, department, eid, **kw):
    return Employee.objects.create(
        company=company, department=department, employee_id=eid,
        first_name="Emp", last_name=eid, date_of_joining=date(2025, 1, 1), **kw
    )


@pytest.mark.django_db
class TestSalaryConfidentiality:
    """HR-CTRL-001 — access restriction. Encryption at rest is deliberately
    not claimed; see the mixin docstring."""

    @pytest.fixture
    def employee(self, company, department):
        return make_employee(company, department, "SAL-1", salary=Decimal("20000"))

    def test_hr_manager_sees_salary(self, api_client, django_user_model, employee, company):
        api_client.force_authenticate(user_with_role(django_user_model, "hr@x.com", "HR Manager", company))
        response = api_client.get(f"/api/hr/employees/{employee.pk}/")
        assert "salary" in response.data

    def test_finance_sees_salary(self, api_client, django_user_model, employee, company):
        api_client.force_authenticate(user_with_role(django_user_model, "cfo2@x.com", "CFO", company))
        response = api_client.get(f"/api/hr/employees/{employee.pk}/")
        assert "salary" in response.data

    def test_ordinary_user_does_not(self, api_client, django_user_model, employee, company):
        api_client.force_authenticate(user_with_role(django_user_model, "clerk2@x.com", "Clerk", company))
        response = api_client.get(f"/api/hr/employees/{employee.pk}/")
        assert "salary" not in response.data
        assert response.data["employee_id"] == "SAL-1"  # the rest still works

    def test_employee_sees_their_own_salary(
        self, api_client, django_user_model, company, department
    ):
        """Hiding someone's own pay from them isn't confidentiality, it's just
        a broken record."""
        u = user_with_role(django_user_model, "self2@x.com", "Clerk", company)
        e = make_employee(company, department, "SAL-2", salary=Decimal("15000"), user=u)
        api_client.force_authenticate(u)
        response = api_client.get(f"/api/hr/employees/{e.pk}/")
        assert response.data["salary"] == "15000.00"

    def test_employee_cannot_see_a_colleagues_salary(
        self, api_client, django_user_model, company, department, employee
    ):
        u = user_with_role(django_user_model, "peer@x.com", "Clerk", company)
        make_employee(company, department, "SAL-3", salary=Decimal("1"), user=u)
        api_client.force_authenticate(u)
        response = api_client.get(f"/api/hr/employees/{employee.pk}/")
        assert "salary" not in response.data

    def test_payroll_figures_are_masked_too(
        self, api_client, django_user_model, employee, company
    ):
        Payroll.objects.create(
            employee=employee, pay_period_start=date(2026, 1, 1),
            pay_period_end=date(2026, 1, 31), basic_salary=Decimal("20000"),
        )
        api_client.force_authenticate(user_with_role(django_user_model, "nosy@x.com", "Clerk", company))
        response = api_client.get("/api/hr/payrolls/")
        row = response.data["results"][0] if "results" in response.data else response.data[0]
        for f in ("basic_salary", "net_salary", "gross_salary"):
            assert f not in row

    def test_superuser_sees_everything(self, api_client, django_user_model, employee):
        su = django_user_model.objects.create_superuser(email="su2@x.com", password="testpass123")
        api_client.force_authenticate(su)
        response = api_client.get(f"/api/hr/employees/{employee.pk}/")
        assert "salary" in response.data


@pytest.mark.django_db
class TestHiringApproval:
    """HR-CTRL-002."""

    @pytest.fixture
    def head(self, company, department):
        return make_employee(company, department, "HEAD-1")

    def test_new_hire_without_approvals_cannot_activate(self, company, department):
        e = Employee(
            company=company, department=department, employee_id="NEW-1",
            first_name="New", last_name="Hire", date_of_joining=date.today(),
            status="Active",
        )
        with pytest.raises(ValidationError, match="requires approval"):
            e.check_hiring_approval()

    def test_missing_hr_approval_is_named(self, company, department, head):
        e = Employee(
            company=company, department=department, employee_id="NEW-2",
            first_name="New", last_name="Hire", date_of_joining=date.today(),
            approved_by_dept_head=head,
        )
        with pytest.raises(ValidationError, match="HR"):
            e.check_hiring_approval()

    def test_both_approvals_allow_activation(
        self, company, department, head, django_user_model
    ):
        e = Employee(
            company=company, department=department, employee_id="NEW-3",
            first_name="New", last_name="Hire", date_of_joining=date.today(),
            approved_by_dept_head=head,
            approved_by_hr=user_with_role(django_user_model, "hr3@x.com", "HR Manager"),
        )
        e.check_hiring_approval()

    def test_existing_employees_are_grandfathered(self, company, department):
        """They predate the control and were never routed through it."""
        e = make_employee(company, department, "OLD-1", status="Active")
        e.status = "On Leave"
        e.save()
        e.status = "Active"
        e.check_hiring_approval()  # must not raise

    def test_api_blocks_activation_of_an_unapproved_hire(
        self, api_client, django_user_model, company, department
    ):
        su = django_user_model.objects.create_superuser(email="su3@x.com", password="testpass123")
        api_client.force_authenticate(su)
        e = make_employee(company, department, "NEW-4", status="Pending Approval")
        response = api_client.patch(f"/api/hr/employees/{e.pk}/", {"status": "Active"}, format="json")
        assert response.status_code == 400
        e.refresh_from_db()
        assert e.status == "Pending Approval"


@pytest.mark.django_db
class TestTerminationAudit:
    """HR-CTRL-004."""

    @pytest.fixture
    def employee(self, company, department):
        return make_employee(company, department, "TERM-1", status="Active")

    @pytest.fixture
    def manager(self, company, department, django_user_model):
        return make_employee(
            company, department, "MGR-1",
            user=user_with_role(django_user_model, "mgr2@x.com", "Manager"),
        )

    def termination(self, employee, **kw):
        return EmployeeTermination.objects.create(
            employee=employee, termination_date=date.today(),
            reason=kw.pop("reason", "Resignation"), **kw
        )

    def test_termination_records_reason_and_chain(
        self, employee, manager, django_user_model
    ):
        hr = user_with_role(django_user_model, "hr4@x.com", "HR Manager")
        t = self.termination(
            employee, reason="Redundancy", reason_detail="Role closed",
            approved_by_manager=manager, approved_by_hr=hr,
        )
        t.approve()
        employee.refresh_from_db()
        assert employee.status == "Terminated"
        assert t.status == "Approved" and t.reason == "Redundancy"

    def test_unapproved_termination_cannot_complete(self, employee):
        t = self.termination(employee)
        with pytest.raises(ValidationError, match="requires approval"):
            t.approve()

    def test_manager_only_is_not_a_chain(self, employee, manager):
        t = self.termination(employee, approved_by_manager=manager)
        with pytest.raises(ValidationError, match="HR"):
            t.approve()

    def test_one_person_cannot_sign_both_roles(self, employee, manager):
        t = self.termination(
            employee, approved_by_manager=manager, approved_by_hr=manager.user
        )
        with pytest.raises(ValidationError, match="two different people"):
            t.approve()

    def test_cannot_approve_twice(self, employee, manager, django_user_model):
        hr = user_with_role(django_user_model, "hr5@x.com", "HR Manager")
        t = self.termination(employee, approved_by_manager=manager, approved_by_hr=hr)
        t.approve()
        with pytest.raises(ValidationError, match="Only a pending"):
            t.approve()

    def test_the_log_survives_the_employee_record(
        self, employee, manager, django_user_model
    ):
        hr = user_with_role(django_user_model, "hr6@x.com", "HR Manager")
        t = self.termination(employee, approved_by_manager=manager, approved_by_hr=hr)
        t.approve()
        assert EmployeeTermination.objects.filter(employee=employee).count() == 1

    def test_api_records_the_requester(self, api_client, django_user_model, employee):
        su = django_user_model.objects.create_superuser(email="su4@x.com", password="testpass123")
        api_client.force_authenticate(su)
        response = api_client.post("/api/hr/terminations/", {
            "employee": employee.pk, "termination_date": str(date.today()),
            "reason": "Resignation",
        }, format="json")
        assert response.status_code == 201
        assert EmployeeTermination.objects.get(pk=response.data["id"]).requested_by == su
