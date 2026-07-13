"""Pytest tests for the Accounting module (apps.accounts).

Covers the highest-risk untested module flagged in the project review
(تقرير_مراجعة_Nexus-Framework.md, P1 #4): double-entry posting, trial
balance, financial statements, general ledger, and budget variance.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Account, Budget, CostCenter, JournalEntry
from apps.core.models import CompanyProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="accountant@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Acme Inc", code="ACME")


@pytest.fixture
def cash_account(company):
    return Account.objects.create(
        company=company,
        account_name="Cash",
        account_number="1000",
        account_type="Asset",
        root_type="Asset",
    )


@pytest.fixture
def revenue_account(company):
    return Account.objects.create(
        company=company,
        account_name="Sales Revenue",
        account_number="4000",
        account_type="Income",
        root_type="Income",
    )


@pytest.fixture
def expense_account(company):
    return Account.objects.create(
        company=company,
        account_name="Office Expense",
        account_number="5000",
        account_type="Expense",
        root_type="Expense",
    )


@pytest.mark.django_db
class TestAccountModel:
    def test_asset_account_increases_with_debit(self, cash_account):
        cash_account.post(debit_amount=1000)
        cash_account.refresh_from_db()
        assert cash_account.balance == 1000

    def test_asset_account_decreases_with_credit(self, cash_account):
        cash_account.post(debit_amount=1000)
        cash_account.post(credit_amount=400)
        cash_account.refresh_from_db()
        assert cash_account.balance == 600

    def test_income_account_increases_with_credit(self, revenue_account):
        revenue_account.post(credit_amount=500)
        revenue_account.refresh_from_db()
        assert revenue_account.balance == 500

    def test_income_account_decreases_with_debit(self, revenue_account):
        revenue_account.post(credit_amount=500)
        revenue_account.post(debit_amount=200)
        revenue_account.refresh_from_db()
        assert revenue_account.balance == 300


@pytest.mark.django_db
class TestJournalEntryPosting:
    def test_simple_two_account_entry_posts_on_submit(
        self, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-001",
            posting_date="2026-01-01",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=1000,
            status="Draft",
        )
        entry.post_to_ledger()
        cash_account.refresh_from_db()
        revenue_account.refresh_from_db()
        assert cash_account.balance == 1000
        assert revenue_account.balance == 1000

    def test_multi_line_entry_posts_each_line(
        self, cash_account, revenue_account, expense_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-002",
            posting_date="2026-01-02",
            status="Draft",
        )
        entry.lines.create(account=cash_account, debit=800)
        entry.lines.create(account=expense_account, debit=200)
        entry.lines.create(account=revenue_account, credit=1000)
        entry.post_to_ledger()
        cash_account.refresh_from_db()
        expense_account.refresh_from_db()
        revenue_account.refresh_from_db()
        assert cash_account.balance == 800
        assert expense_account.balance == 200
        assert revenue_account.balance == 1000

    def test_cannot_post_to_group_account(self, revenue_account, company):
        group_account = Account.objects.create(
            company=company,
            account_name="Current Assets",
            account_number="1900",
            account_type="Asset",
            root_type="Asset",
            is_group=True,
        )
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-003",
            posting_date="2026-01-03",
            debit_account=group_account,
            credit_account=revenue_account,
            amount=100,
            status="Draft",
        )
        with pytest.raises(Exception):
            entry.post_to_ledger()


@pytest.mark.django_db
class TestJournalEntryAPI:
    def test_submitting_unbalanced_multi_line_entry_is_rejected(
        self, auth_client, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-100",
            posting_date="2026-01-05",
            status="Draft",
        )
        entry.lines.create(account=cash_account, debit=800)
        entry.lines.create(account=revenue_account, credit=500)
        response = auth_client.patch(
            f"/api/accounts/journal-entries/{entry.id}/",
            {"status": "Submitted", "total_debit": "800", "total_credit": "500"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submitting_balanced_entry_posts_to_accounts(
        self, auth_client, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-101",
            posting_date="2026-01-06",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=750,
            status="Draft",
        )
        response = auth_client.patch(
            f"/api/accounts/journal-entries/{entry.id}/", {"status": "Submitted"}
        )
        assert response.status_code == status.HTTP_200_OK
        cash_account.refresh_from_db()
        revenue_account.refresh_from_db()
        assert cash_account.balance == 750
        assert revenue_account.balance == 750

    def test_same_debit_and_credit_account_rejected(self, auth_client, cash_account, company):
        response = auth_client.post(
            "/api/accounts/journal-entries/",
            {
                "company": str(company.id),
                "entry_number": "JE-102",
                "posting_date": "2026-01-07",
                "debit_account": cash_account.id,
                "credit_account": cash_account.id,
                "amount": "100",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resubmitting_already_submitted_entry_is_rejected(
        self, auth_client, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-103",
            posting_date="2026-01-08",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=100,
            status="Submitted",
        )
        response = auth_client.patch(
            f"/api/accounts/journal-entries/{entry.id}/", {"status": "Draft"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/accounts/journal-entries/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTrialBalanceAndFinancialStatements:
    def test_trial_balance_is_balanced_after_posting(
        self, auth_client, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-200",
            posting_date="2026-02-01",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=2000,
            status="Draft",
        )
        entry.post_to_ledger()
        response = auth_client.get("/api/accounts/accounts/trial_balance/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["balanced"] is True
        assert response.data["total_debit"] == response.data["total_credit"]

    def test_financial_statements_reflect_posted_entries(
        self, auth_client, cash_account, revenue_account, expense_account, company
    ):
        income_entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-201",
            posting_date="2026-02-02",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=5000,
            status="Draft",
        )
        income_entry.post_to_ledger()
        expense_entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-202",
            posting_date="2026-02-03",
            debit_account=expense_account,
            credit_account=cash_account,
            amount=1200,
            status="Draft",
        )
        expense_entry.post_to_ledger()

        response = auth_client.get("/api/accounts/accounts/financial_statements/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_statement"]["total_income"] == 5000
        assert response.data["income_statement"]["total_expense"] == 1200
        assert response.data["income_statement"]["net_income"] == 3800
        assert response.data["balance_sheet"]["total_assets"] == 3800

    def test_general_ledger_running_balance(
        self, auth_client, cash_account, revenue_account, company
    ):
        entry = JournalEntry.objects.create(
            company=company,
            entry_number="JE-203",
            posting_date="2026-02-04",
            debit_account=cash_account,
            credit_account=revenue_account,
            amount=300,
            status="Draft",
        )
        entry.post_to_ledger()
        response = auth_client.get(
            f"/api/accounts/accounts/{cash_account.id}/general_ledger/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["closing_balance"] == 300
        assert len(response.data["rows"]) == 1


@pytest.mark.django_db
class TestBudget:
    def test_budget_variance_and_percentage(self, cash_account, company):
        budget = Budget.objects.create(
            company=company,
            name="Q1 Cash Budget",
            fiscal_year="2026",
            account=cash_account,
            budget_amount=1000,
            actual_amount=1250,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        assert budget.variance == 250
        assert budget.variance_percentage == 25

    def test_budget_zero_budget_amount_percentage_is_safe(self, cash_account, company):
        budget = Budget.objects.create(
            company=company,
            name="Empty Budget",
            fiscal_year="2026",
            account=cash_account,
            budget_amount=0,
            actual_amount=100,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        assert budget.variance_percentage == 0

    def test_invalid_status_transition_rejected(self, auth_client, cash_account, company):
        budget = Budget.objects.create(
            company=company,
            name="Closed Budget",
            fiscal_year="2026",
            account=cash_account,
            budget_amount=100,
            actual_amount=0,
            status="Closed",
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        response = auth_client.patch(
            f"/api/accounts/budgets/{budget.id}/", {"status": "Active"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_end_date_before_start_date_rejected(self, auth_client, cash_account, company):
        response = auth_client.post(
            "/api/accounts/budgets/",
            {
                "company": str(company.id),
                "name": "Bad Dates",
                "fiscal_year": "2026",
                "account": cash_account.id,
                "budget_amount": "100",
                "start_date": "2026-06-01",
                "end_date": "2026-01-01",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCostCenter:
    def test_create_cost_center(self, auth_client, company):
        response = auth_client.post(
            "/api/accounts/cost-centers/",
            {"company": str(company.id), "name": "Operations"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_nested_cost_centers(self, company):
        parent = CostCenter.objects.create(company=company, name="Head Office")
        child = CostCenter.objects.create(
            company=company, name="Branch A", parent_cost_center=parent
        )
        assert child.parent_cost_center == parent
