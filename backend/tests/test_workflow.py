"""BPM workflow engine — state machines for documents.

A workflow is states connected by transitions; a document attaches as an
instance sitting in one state, moving along transitions that can require a role.
More general than the approval ladder: an arbitrary graph, not a linear chain.
"""
import pytest
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import CompanyProfile
from apps.rbac.models import Role, RoleAssignment
from apps.workflow.models import State, Transition, Workflow, WorkflowInstance


@pytest.fixture
def users(db, django_user_model):
    clerk = django_user_model.objects.create_user(email="clerk@x.com", password="x")
    mgr = django_user_model.objects.create_user(email="mgr@x.com", password="x")
    role = Role.objects.create(name="Manager")
    RoleAssignment.objects.create(user=mgr, role=role)
    return {"clerk": clerk, "mgr": mgr, "role": role}


@pytest.fixture
def workflow(db, users):
    wf = Workflow.objects.create(name="PO approval", document_type="purchase_order")
    draft = State.objects.create(workflow=wf, key="draft", label="Draft", is_initial=True)
    sub = State.objects.create(workflow=wf, key="submitted", label="Submitted")
    app = State.objects.create(workflow=wf, key="approved", label="Approved", is_final=True)
    rej = State.objects.create(workflow=wf, key="rejected", label="Rejected", is_final=True)
    Transition.objects.create(workflow=wf, name="Submit", from_state=draft, to_state=sub)
    Transition.objects.create(workflow=wf, name="Approve", from_state=sub, to_state=app, required_role=users["role"])
    Transition.objects.create(workflow=wf, name="Reject", from_state=sub, to_state=rej, required_role=users["role"])
    return wf


@pytest.fixture
def po(db):
    c = CompanyProfile.objects.create(name="A", code="AC")
    sup = Supplier.objects.create(company=c, name="S")
    return PurchaseOrder.objects.create(company=c, supplier=sup, po_number="P1", transaction_date="2026-01-01")


@pytest.mark.django_db
class TestEngine:
    def test_starts_at_initial_state(self, workflow, po):
        inst = WorkflowInstance.start(workflow, po)
        assert inst.current_state.key == "draft"

    def test_start_is_idempotent(self, workflow, po):
        a = WorkflowInstance.start(workflow, po)
        b = WorkflowInstance.start(workflow, po)
        assert a.pk == b.pk

    def test_available_transitions_filtered_by_role(self, workflow, po, users):
        inst = WorkflowInstance.start(workflow, po)
        submit = Transition.objects.get(workflow=workflow, name="Submit")
        inst.take(submit, users["clerk"])
        assert inst.available_transitions(users["clerk"]) == []      # needs manager
        assert len(inst.available_transitions(users["mgr"])) == 2    # approve + reject

    def test_role_gated_transition_refused_without_role(self, workflow, po, users):
        from django.core.exceptions import ValidationError
        inst = WorkflowInstance.start(workflow, po)
        submit = Transition.objects.get(workflow=workflow, name="Submit")
        approve = Transition.objects.get(workflow=workflow, name="Approve")
        inst.take(submit, users["clerk"])
        with pytest.raises(ValidationError):
            inst.take(approve, users["clerk"])

    def test_cannot_take_transition_from_wrong_state(self, workflow, po, users):
        from django.core.exceptions import ValidationError
        inst = WorkflowInstance.start(workflow, po)
        approve = Transition.objects.get(workflow=workflow, name="Approve")
        with pytest.raises(ValidationError):  # can't approve straight from draft
            inst.take(approve, users["mgr"])

    def test_full_path_and_history(self, workflow, po, users):
        inst = WorkflowInstance.start(workflow, po)
        submit = Transition.objects.get(workflow=workflow, name="Submit")
        approve = Transition.objects.get(workflow=workflow, name="Approve")
        inst.take(submit, users["clerk"])
        inst.take(approve, users["mgr"])
        assert inst.current_state.key == "approved"
        assert inst.current_state.is_final
        assert inst.available_transitions(users["mgr"]) == []  # nothing out of final
        assert inst.history.count() == 2


@pytest.mark.django_db
class TestWorkflowAPI:
    def _admin(self, django_user_model):
        c = APIClient()
        c.force_authenticate(django_user_model.objects.create_superuser(email="a@x.com", password="x"))
        return c

    def test_create_workflow_with_states(self, db, django_user_model):
        c = self._admin(django_user_model)
        r = c.post("/api/workflow/workflows/", {
            "name": "Simple", "document_type": "invoice",
            "states": [{"key": "draft", "label": "Draft", "is_initial": True},
                       {"key": "done", "label": "Done", "is_final": True}],
        }, format="json")
        assert r.status_code == 201, r.data
        assert len(r.data["states"]) == 2

    def test_take_transition_via_api(self, workflow, po, users):
        from apps.tenants.models import Tenant
        t = Tenant.objects.create(name="T", slug="t", subdomain="t")
        users["clerk"].tenant = t
        users["clerk"].save()
        inst = WorkflowInstance.start(workflow, po, tenant=t)
        submit = Transition.objects.get(workflow=workflow, name="Submit")
        c = APIClient()
        c.force_authenticate(users["clerk"])
        r = c.post(f"/api/workflow/instances/{inst.id}/take/",
                   {"transition": submit.id}, format="json")
        assert r.status_code == 200
        assert r.data["state_key"] == "submitted"
