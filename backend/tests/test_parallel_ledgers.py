"""Parallel ledgers — simultaneous reporting under multiple standards.

One business event can be reported differently under IFRS and local GAAP (and
tax, and management). A LedgerPosting records how a source entry lands in one
ledger, so the same entry can carry a different amount per ledger, and each
ledger reports independently. Additive: the leading ledger mirrors the existing
single-ledger path.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.models import Account, Ledger, post_to_ledgers
from apps.core.models import CompanyProfile


@pytest.fixture
def setup(db):
    c = CompanyProfile.objects.create(name="Corp", code="CO")
    ifrs = Ledger.objects.create(company=c, code="IFRS", name="IFRS", standard="ifrs", is_leading=True)
    gaap = Ledger.objects.create(company=c, code="GAAP", name="Local GAAP", standard="local_gaap")
    asset = Account.objects.create(company=c, account_name="Equipment", account_number="1500", account_type="Asset")
    return dict(c=c, ifrs=ifrs, gaap=gaap, asset=asset)


@pytest.mark.django_db
class TestLedgerDefinition:
    def test_only_one_leading_ledger_per_company(self, setup):
        with pytest.raises(IntegrityError):
            Ledger.objects.create(company=setup["c"], code="TAX", name="Tax",
                                   standard="tax", is_leading=True)

    def test_ledger_code_unique_per_company(self, setup):
        with pytest.raises(IntegrityError):
            Ledger.objects.create(company=setup["c"], code="IFRS", name="dup", standard="tax")


@pytest.mark.django_db
class TestParallelPosting:
    def test_same_event_different_amounts_per_ledger(self, setup):
        posts = post_to_ledgers(
            company=setup["c"], account=setup["asset"], posting_date=date(2026, 1, 31),
            debit=1000, credit=0, ledger_amounts={"GAAP": (1200, 0)},
        )
        assert len(posts) == 2
        assert setup["ifrs"].balance_for(setup["asset"]) == Decimal("1000")
        assert setup["gaap"].balance_for(setup["asset"]) == Decimal("1200")

    def test_default_amount_applies_to_unnamed_ledgers(self, setup):
        post_to_ledgers(company=setup["c"], account=setup["asset"],
                        posting_date=date(2026, 1, 31), debit=500, credit=0)
        assert setup["ifrs"].balance_for(setup["asset"]) == Decimal("500")
        assert setup["gaap"].balance_for(setup["asset"]) == Decimal("500")

    def test_ledgers_are_independent(self, setup):
        post_to_ledgers(company=setup["c"], account=setup["asset"],
                        posting_date=date(2026, 1, 31), debit=1000, credit=0,
                        ledger_amounts={"GAAP": (0, 0)})
        # GAAP got nothing; IFRS got 1000. They don't leak into each other.
        assert setup["ifrs"].balance_for(setup["asset"]) == Decimal("1000")
        assert setup["gaap"].balance_for(setup["asset"]) == Decimal("0")

    def test_inactive_ledger_is_skipped(self, setup):
        setup["gaap"].is_active = False
        setup["gaap"].save()
        posts = post_to_ledgers(company=setup["c"], account=setup["asset"],
                                posting_date=date(2026, 1, 31), debit=100, credit=0)
        assert len(posts) == 1  # only IFRS
        assert posts[0].ledger.code == "IFRS"


@pytest.mark.django_db
class TestLedgerAPI:
    def _admin(self, django_user_model):
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(django_user_model.objects.create_superuser(email="a@x.com", password="x"))
        return c

    def test_trial_balance_is_per_ledger(self, setup, django_user_model):
        post_to_ledgers(company=setup["c"], account=setup["asset"],
                        posting_date=date(2026, 1, 31), debit=1000, credit=0,
                        ledger_amounts={"GAAP": (1200, 0)})
        c = self._admin(django_user_model)
        r = c.get(f"/api/accounts/ledgers/{setup['gaap'].id}/trial_balance/")
        assert r.status_code == 200
        assert r.data["ledger"] == "GAAP"
        assert Decimal(str(r.data["rows"][0]["debit"])) == Decimal("1200")
