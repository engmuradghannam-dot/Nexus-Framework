"""Tests for the governance rules/controls from ERP_Complete_System.xlsx.

Covers FIN-CTRL-001 (dual authorization), FIN-CTRL-002 (segregation of duties
on journal entries), HR-CTRL-003 (leave balance), CRM-CTRL-002 (duplicate
party prevention) and INV-RULE-005 (expiry alerts).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Account, JournalEntry
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.hr.models import Department, Employee, LeaveRequest
from apps.inventory.models import Item, ItemBatch
from apps.rbac.models import Role, RoleAssignment
from apps.selling.models import Customer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Gov Co", code="GOV-CO")


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="gov@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


def user_with_role(django_user_model, email, role_name):
    u = django_user_model.objects.create_user(email=email, password="testpass123")
    RoleAssignment.objects.create(
        user=u, role=Role.objects.get_or_create(name=role_name, defaults={"permissions": {}})[0]
    )
    return u


@pytest.fixture
def accounts(company):
    dr = Account.objects.create(company=company, account_number="1000", account_name="Cash", account_type="Asset")
    cr = Account.objects.create(company=company, account_number="4000", account_name="Revenue", account_type="Revenue")
    return dr, cr


def make_je(company, accounts, amount, number="JE-1"):
    dr, cr = accounts
    return JournalEntry.objects.create(
        company=company, entry_number=number, posting_date=date(2026, 1, 10),
        debit_account=dr, credit_account=cr, amount=Decimal(amount),
        total_debit=Decimal(amount), total_credit=Decimal(amount), status="Draft",
    )


@pytest.mark.django_db
class TestDualAuthorization:
    """FIN-CTRL-001: above 50,000 SAR needs Finance Manager + CFO."""

    def test_below_threshold_needs_no_dual_approval(self, company, accounts):
        je = make_je(company, accounts, 10000)
        assert je.needs_dual_authorization is False
        je.check_authorization()

    def test_at_threshold_is_not_dual(self, company, accounts):
        je = make_je(company, accounts, 50000)
        assert je.needs_dual_authorization is False

    def test_above_threshold_without_approvers_blocked(self, company, accounts):
        je = make_je(company, accounts, 50001)
        assert je.needs_dual_authorization is True
        with pytest.raises(ValidationError, match="dual authorization"):
            je.check_authorization()

    def test_single_approver_is_not_enough(self, company, accounts, django_user_model):
        je = make_je(company, accounts, 90000)
        je.approved_by = user_with_role(django_user_model, "fm@x.com", "Finance Manager")
        with pytest.raises(ValidationError, match="dual authorization"):
            je.check_authorization()

    def test_two_correct_roles_pass(self, company, accounts, django_user_model):
        je = make_je(company, accounts, 90000)
        je.approved_by = user_with_role(django_user_model, "fm@x.com", "Finance Manager")
        je.second_approved_by = user_with_role(django_user_model, "cfo@x.com", "CFO")
        je.check_authorization()

    def test_same_user_twice_rejected(self, company, accounts, django_user_model):
        u = user_with_role(django_user_model, "both@x.com", "Finance Manager")
        je = make_je(company, accounts, 90000)
        je.approved_by = u
        je.second_approved_by = u
        with pytest.raises(ValidationError, match="two different approvers"):
            je.check_authorization()

    def test_one_user_holding_both_roles_is_not_two_people(
        self, company, accounts, django_user_model
    ):
        both = user_with_role(django_user_model, "super@x.com", "Finance Manager")
        RoleAssignment.objects.create(
            user=both, role=Role.objects.get_or_create(name="CFO", defaults={"permissions": {}})[0]
        )
        other = user_with_role(django_user_model, "clerk@x.com", "Clerk")
        je = make_je(company, accounts, 90000)
        je.approved_by = both
        je.second_approved_by = other
        # `other` holds neither required role, so `both` would have to stand in
        # for two people — which is exactly what dual authorization forbids.
        with pytest.raises(ValidationError, match="not sufficient"):
            je.check_authorization()

    def test_wrong_roles_rejected(self, company, accounts, django_user_model):
        je = make_je(company, accounts, 90000)
        je.approved_by = user_with_role(django_user_model, "a@x.com", "Clerk")
        je.second_approved_by = user_with_role(django_user_model, "b@x.com", "Intern")
        with pytest.raises(ValidationError, match="missing"):
            je.check_authorization()

    def test_fin_ctrl_002_creator_cannot_approve_even_small_entries(
        self, company, accounts, django_user_model
    ):
        u = user_with_role(django_user_model, "self@x.com", "Finance Manager")
        je = make_je(company, accounts, 100)
        je.posted_by = u
        je.approved_by = u
        with pytest.raises(ValidationError, match="Segregation of duties"):
            je.check_authorization()


@pytest.mark.django_db
class TestLeaveBalance:
    """HR-CTRL-003: 21 days annual, and nothing beyond it."""

    @pytest.fixture
    def employee(self, company):
        dept = Department.objects.create(company=company, name="Ops")
        return Employee.objects.create(
            company=company, department=dept, employee_id="LV-1",
            first_name="Leave", last_name="Taker", date_of_joining=date(2025, 1, 1),
        )

    def _leave(self, employee, start, days, status="Approved"):
        return LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2026,
            start_date=start, end_date=start + timedelta(days=days - 1), status=status,
        )

    def test_within_balance_passes(self, employee):
        lr = self._leave(employee, date(2026, 2, 1), 5, status="Pending")
        lr.check_balance()

    def test_exceeding_balance_blocked(self, employee):
        lr = self._leave(employee, date(2026, 2, 1), 25, status="Pending")
        with pytest.raises(ValidationError, match="Insufficient leave balance"):
            lr.check_balance()

    def test_previously_approved_leave_counts_against_the_balance(self, employee):
        self._leave(employee, date(2026, 1, 1), 18)
        lr = self._leave(employee, date(2026, 3, 1), 5, status="Pending")
        with pytest.raises(ValidationError, match="3 day"):
            lr.check_balance()

    def test_sick_leave_is_not_capped_by_the_annual_balance(self, employee):
        lr = LeaveRequest.objects.create(
            employee=employee, leave_type="Sick", year=2026,
            start_date=date(2026, 2, 1), end_date=date(2026, 4, 1), status="Pending",
        )
        lr.check_balance()  # must not raise

    def test_another_year_has_its_own_balance(self, employee):
        self._leave(employee, date(2026, 1, 1), 21)
        lr = LeaveRequest.objects.create(
            employee=employee, leave_type="Annual", year=2027,
            start_date=date(2027, 1, 1), end_date=date(2027, 1, 5), status="Pending",
        )
        lr.check_balance()


@pytest.mark.django_db
class TestDuplicateParty:
    """CRM-CTRL-002."""

    def test_duplicate_email_flagged(self, auth_client, company):
        Customer.objects.create(company=company, name="Acme", email="hi@acme.sa")
        response = auth_client.post("/api/selling/customers/", {
            "company": company.pk, "name": "Acme Trading", "email": "hi@acme.sa",
        }, format="json")
        assert response.status_code == 400
        assert "duplicate" in str(response.data).lower()

    def test_email_match_is_case_insensitive(self, auth_client, company):
        Customer.objects.create(company=company, name="Acme", email="hi@acme.sa")
        response = auth_client.post("/api/selling/customers/", {
            "company": company.pk, "name": "Acme 2", "email": "HI@ACME.SA",
        }, format="json")
        assert response.status_code == 400

    def test_duplicate_phone_flagged(self, auth_client, company):
        Customer.objects.create(company=company, name="Acme", phone="0551234567")
        response = auth_client.post("/api/selling/customers/", {
            "company": company.pk, "name": "Acme 2", "phone": "0551234567",
        }, format="json")
        assert response.status_code == 400

    def test_blank_contact_details_do_not_collide(self, auth_client, company):
        Customer.objects.create(company=company, name="No Contact")
        response = auth_client.post("/api/selling/customers/", {
            "company": company.pk, "name": "Also No Contact",
        }, format="json")
        assert response.status_code == 201

    def test_same_email_in_a_different_company_is_allowed(self, auth_client, company):
        other = CompanyProfile.objects.create(name="Other", code="OTH-D")
        Customer.objects.create(company=other, name="Acme", email="hi@acme.sa")
        response = auth_client.post("/api/selling/customers/", {
            "company": company.pk, "name": "Acme", "email": "hi@acme.sa",
        }, format="json")
        assert response.status_code == 201

    def test_editing_a_customer_does_not_flag_itself(self, auth_client, company):
        c = Customer.objects.create(company=company, name="Acme", email="hi@acme.sa")
        response = auth_client.patch(
            f"/api/selling/customers/{c.pk}/", {"name": "Acme Ltd"}, format="json"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestExpiryAlerts:
    """INV-RULE-005: 30-day horizon."""

    @pytest.fixture
    def setup(self, company):
        branch = Branch.objects.create(company=company, name="B", code="EXP-B", address="Riyadh")
        wh = Warehouse.objects.get(branch=branch)
        item = Item.objects.create(company=company, item_code="E-1", item_name="Milk")
        return wh, item

    def test_batch_expiring_within_30_days_flagged(self, setup):
        wh, item = setup
        b = ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="B1", quantity=5,
            expiry_date=date.today() + timedelta(days=10),
        )
        assert b.is_expiring_soon is True
        assert b.is_expired is False
        assert b.days_to_expiry == 10

    def test_batch_beyond_30_days_not_flagged(self, setup):
        wh, item = setup
        b = ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="B2", quantity=5,
            expiry_date=date.today() + timedelta(days=60),
        )
        assert b.is_expiring_soon is False

    def test_already_expired_is_flagged(self, setup):
        wh, item = setup
        b = ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="B3", quantity=5,
            expiry_date=date.today() - timedelta(days=2),
        )
        assert b.is_expiring_soon is True
        assert b.is_expired is True

    def test_undated_batch_never_alerts(self, setup):
        wh, item = setup
        b = ItemBatch.objects.create(item=item, warehouse=wh, batch_no="B4", quantity=5)
        assert b.days_to_expiry is None
        assert b.is_expiring_soon is False

    def test_api_lists_expiring_batches(self, auth_client, setup):
        wh, item = setup
        ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="SOON", quantity=5,
            expiry_date=date.today() + timedelta(days=10),
        )
        ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="LATER", quantity=5,
            expiry_date=date.today() + timedelta(days=200),
        )
        response = auth_client.get("/api/records/expiring_batches/")
        assert response.status_code == 200
        assert [a["batch_no"] for a in response.data["alerts"]] == ["SOON"]

    def test_api_is_company_scoped(self, api_client, django_user_model, setup, company):
        wh, item = setup
        ItemBatch.objects.create(
            item=item, warehouse=wh, batch_no="MINE", quantity=5,
            expiry_date=date.today() + timedelta(days=5),
        )
        outsider = django_user_model.objects.create_user(
            email="outsider@x.com", password="testpass123"
        )
        api_client.force_authenticate(user=outsider)
        response = api_client.get("/api/records/expiring_batches/")
        assert response.data["alerts"] == []
