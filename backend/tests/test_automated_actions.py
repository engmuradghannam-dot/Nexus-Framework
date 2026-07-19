"""Automated actions — no-code 'on event, if condition, do something' rules.

The condition is a safe three-part comparison (field, operator, value), never
eval(). Steps do one concrete thing each. A failing step is recorded and skipped
— an automation must never break the operation that triggered it.
"""
from decimal import Decimal

import pytest

from apps.automation.actions import compare, fire_event
from apps.automation.models import AutomatedAction, AutomatedActionStep
from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import CompanyProfile


@pytest.fixture
def po_factory(db):
    c = CompanyProfile.objects.create(name="A", code="AC")
    sup = Supplier.objects.create(company=c, name="S")
    n = {"i": 0}

    def make(total):
        n["i"] += 1
        return PurchaseOrder.objects.create(
            company=c, supplier=sup, po_number=f"P{n['i']}",
            transaction_date="2026-01-01", grand_total=Decimal(str(total)),
        )
    return make


@pytest.mark.django_db
class TestSafeComparator:
    @pytest.mark.parametrize("a,op,v,expected", [
        (15000, ">", "10000", True),
        (5000, ">", "10000", False),
        ("posted", "==", "posted", True),
        (Decimal("100"), ">=", "100", True),
        (Decimal("99"), ">=", "100", False),
    ])
    def test_comparisons(self, a, op, v, expected):
        assert compare(a, op, v) is expected

    def test_unknown_operator_is_false_not_raise(self):
        assert compare(1, "__import__", "x") is False
        assert compare(1, "exec", "1") is False


@pytest.mark.django_db
class TestRuleFiring:
    def _rule(self, **kw):
        defaults = dict(name="R", model_label="buying.PurchaseOrder", trigger="on_create")
        defaults.update(kw)
        return AutomatedAction.objects.create(**defaults)

    def test_condition_gates_the_action(self, po_factory):
        act = self._rule(condition_field="grand_total", condition_operator=">",
                         condition_value="10000")
        AutomatedActionStep.objects.create(action=act, step_type="set_field",
                                           target_field="notes", target_value="review")
        assert len(fire_event(po_factory(5000), created=True)) == 0   # condition fails
        big = po_factory(50000)
        assert len(fire_event(big, created=True)) == 1                # condition holds
        big.refresh_from_db()
        assert big.notes == "review"

    def test_no_condition_always_fires(self, po_factory):
        act = self._rule()
        AutomatedActionStep.objects.create(action=act, step_type="set_field",
                                           target_field="notes", target_value="x")
        assert len(fire_event(po_factory(1), created=True)) == 1

    def test_trigger_type_is_respected(self, po_factory):
        self._rule(trigger="on_update")  # only on update
        po = po_factory(100)
        assert len(fire_event(po, created=True)) == 0   # this is a create
        assert len(fire_event(po, created=False)) == 1  # now it's an update

    def test_failing_step_does_not_break_the_operation(self, po_factory):
        act = self._rule()
        AutomatedActionStep.objects.create(action=act, step_type="set_field",
                                           target_field="does_not_exist", target_value="x")
        # Must not raise.
        fire_event(po_factory(1), created=True)

    def test_run_count_increments(self, po_factory):
        act = self._rule()
        AutomatedActionStep.objects.create(action=act, step_type="notify", message="hi {id}")
        fire_event(po_factory(1), created=True)
        act.refresh_from_db()
        assert act.run_count == 1


@pytest.mark.django_db
class TestAutomationAPI:
    def test_create_rule_with_steps(self, db, django_user_model):
        from rest_framework.test import APIClient
        admin = django_user_model.objects.create_superuser(email="a@x.com", password="x")
        c = APIClient()
        c.force_authenticate(admin)
        r = c.post("/api/automation/automated-actions/", {
            "name": "Big POs", "model_label": "buying.PurchaseOrder",
            "trigger": "on_create", "condition_field": "grand_total",
            "condition_operator": ">", "condition_value": "10000",
            "steps": [{"order": 1, "step_type": "set_field",
                       "target_field": "notes", "target_value": "review"}],
        }, format="json")
        assert r.status_code == 201, r.data
        assert len(r.data["steps"]) == 1
