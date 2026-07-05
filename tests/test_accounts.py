import pytest
from apps.accounts.models import Account, JournalEntry

@pytest.mark.django_db
class TestAccounts:
    def test_create_account(self, company):
        acc = Account.objects.create(
            company=company, 
            account_name='Cash', 
            account_type='Asset', 
            account_number='1000'
        )
        assert acc.account_name == 'Cash'
        assert acc.balance == 0

    def test_journal_entry_balance(self, company):
        je = JournalEntry.objects.create(
            company=company, 
            entry_number='JE-001', 
            posting_date='2024-01-01',
            total_debit=1000, 
            total_credit=1000
        )
        assert je.total_debit == je.total_credit
