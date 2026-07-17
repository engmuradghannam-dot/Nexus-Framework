"""Tests for the project rules from ERP_Complete_System.xlsx.

Covers PRJ-RULE-003 (critical path), PRJ-RULE-002 (burn rate),
PRJ-RULE-005 (closure checklist), PRJ-CTRL-002 (milestone gate) and
PRJ-CTRL-003 (resource allocation).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.pmo.models import Milestone, Project, Task, check_resource_allocation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="pmo@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def project():
    return Project.objects.create(name="Bridge", code="BRG-1", status="Active")


def task(project, title, duration, preds=(), **kw):
    t = Task.objects.create(project=project, title=title, duration_days=duration, **kw)
    if preds:
        t.predecessors.set(preds)
    return t


@pytest.mark.django_db
class TestCriticalPath:
    """PRJ-RULE-003.

    Network used by most tests:
        A(3) -> B(4) -> D(2)
        A(3) -> C(1) -> D(2)
    Longest chain A-B-D = 9 days; C has 3 days of slack.
    """

    @pytest.fixture
    def network(self, project):
        a = task(project, "A", 3)
        b = task(project, "B", 4, preds=[a])
        c = task(project, "C", 1, preds=[a])
        d = task(project, "D", 2, preds=[b, c])
        return project, a, b, c, d

    def test_identifies_the_longest_chain(self, network):
        project, a, b, c, d = network
        critical = project.calculate_critical_path()
        assert [t.title for t in critical] == ["A", "B", "D"]

    def test_project_duration_is_the_longest_chain(self, network):
        project, *_ = network
        project.calculate_critical_path()
        assert project.critical_path_length == 9

    def test_non_critical_task_gets_slack(self, network):
        project, a, b, c, d = network
        project.calculate_critical_path()
        c.refresh_from_db()
        assert c.slack == 3 and c.is_critical is False

    def test_critical_tasks_have_zero_slack(self, network):
        project, a, b, c, d = network
        project.calculate_critical_path()
        for t in (a, b, d):
            t.refresh_from_db()
            assert t.slack == 0 and t.is_critical is True

    def test_early_and_late_windows(self, network):
        project, a, b, c, d = network
        project.calculate_critical_path()
        c.refresh_from_db()
        assert (c.early_start, c.early_finish) == (3, 4)
        assert (c.late_start, c.late_finish) == (6, 7)

    def test_lengthening_a_slack_task_can_shift_the_path(self, network):
        project, a, b, c, d = network
        c.duration_days = 10
        c.save()
        critical = project.calculate_critical_path()
        assert [t.title for t in critical] == ["A", "C", "D"]

    def test_parallel_independent_tasks_are_both_critical_when_equal(self, project):
        task(project, "X", 5)
        task(project, "Y", 5)
        critical = project.calculate_critical_path()
        assert {t.title for t in critical} == {"X", "Y"}

    def test_cancelled_tasks_are_excluded(self, project):
        a = task(project, "A", 3)
        task(project, "Dead", 100, preds=[a], status="Cancelled")
        project.calculate_critical_path()
        assert project.critical_path_length == 3

    def test_dependency_cycle_is_reported_not_hung(self, project):
        a = task(project, "A", 1)
        b = task(project, "B", 1, preds=[a])
        a.predecessors.set([b])
        with pytest.raises(ValidationError, match="cycle"):
            project.calculate_critical_path()

    def test_empty_project_returns_nothing(self, project):
        assert project.calculate_critical_path() == []

    def test_api_returns_the_path(self, auth_client, network):
        project, *_ = network
        response = auth_client.get(f"/api/pmo/projects/{project.pk}/critical_path/")
        assert response.status_code == 200
        assert response.data["duration_days"] == 9
        assert [t["title"] for t in response.data["critical_path"]] == ["A", "B", "D"]


@pytest.mark.django_db
class TestBurnRate:
    """PRJ-RULE-002."""

    def test_burn_rate_is_spend_per_elapsed_day(self):
        p = Project.objects.create(
            name="Burn", code="B-1", budget=Decimal("10000"), spent=Decimal("2000"),
            start_date=date.today() - timedelta(days=10),
        )
        assert p.burn_rate == Decimal("200.00")

    def test_no_start_date_gives_no_burn_rate(self):
        p = Project.objects.create(name="NoStart", code="B-2", spent=Decimal("500"))
        assert p.burn_rate is None

    def test_day_zero_does_not_divide_by_zero(self):
        p = Project.objects.create(
            name="Today", code="B-3", spent=Decimal("500"), start_date=date.today()
        )
        assert p.burn_rate is None

    def test_actual_start_takes_precedence_over_planned(self):
        p = Project.objects.create(
            name="Late", code="B-4", spent=Decimal("400"),
            start_date=date.today() - timedelta(days=100),
            actual_start_date=date.today() - timedelta(days=4),
        )
        assert p.burn_rate == Decimal("100.00")


@pytest.mark.django_db
class TestClosureChecklist:
    """PRJ-RULE-005."""

    def test_open_tasks_block_closure(self, project):
        task(project, "Open", 1, status="To Do")
        assert any("task" in b for b in project.closure_blockers())

    def test_unmet_milestones_block_closure(self, project):
        Milestone.objects.create(project=project, name="Gate 1", target_date=date.today())
        assert any("milestone" in b for b in project.closure_blockers())

    def test_budget_overrun_blocks_closure(self):
        p = Project.objects.create(
            name="Over", code="O-1", budget=Decimal("100"), spent=Decimal("150")
        )
        assert any("overrun" in b for b in p.closure_blockers())

    def test_clean_project_has_no_blockers(self, project):
        task(project, "Done task", 1, status="Done")
        Milestone.objects.create(
            project=project, name="Gate", target_date=date.today(), achieved_date=date.today()
        )
        assert project.closure_blockers() == []


@pytest.mark.django_db
class TestMilestoneGate:
    """PRJ-CTRL-002."""

    def test_task_blocked_while_an_earlier_milestone_is_open(self, project):
        early = Milestone.objects.create(
            project=project, name="Design", target_date=date.today()
        )
        late = Milestone.objects.create(
            project=project, name="Build", target_date=date.today() + timedelta(days=30)
        )
        t = task(project, "Pour concrete", 5, milestone=late)
        with pytest.raises(ValidationError, match="Design"):
            project.check_milestone_gate(t)

    def test_task_allowed_once_the_earlier_gate_is_signed_off(self, project):
        Milestone.objects.create(
            project=project, name="Design", target_date=date.today(),
            achieved_date=date.today(),
        )
        late = Milestone.objects.create(
            project=project, name="Build", target_date=date.today() + timedelta(days=30)
        )
        t = task(project, "Pour concrete", 5, milestone=late)
        project.check_milestone_gate(t)

    def test_task_without_a_milestone_is_ungated(self, project):
        Milestone.objects.create(project=project, name="Design", target_date=date.today())
        t = task(project, "Free work", 1)
        project.check_milestone_gate(t)


@pytest.mark.django_db
class TestResourceAllocation:
    """PRJ-CTRL-003."""

    @pytest.fixture
    def worker(self, django_user_model):
        return django_user_model.objects.create_user(
            email="worker@nexus.com", password="testpass123"
        )

    def test_within_capacity_passes(self, project, worker):
        t = task(
            project, "Light", 5, assignee=worker, estimated_hours=Decimal("20"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
        )
        check_resource_allocation(worker, t)

    def test_over_allocation_blocked(self, project, worker):
        task(
            project, "Existing", 5, assignee=worker, estimated_hours=Decimal("40"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
            status="In Progress",
        )
        t = task(
            project, "New", 5, assignee=worker, estimated_hours=Decimal("20"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
        )
        with pytest.raises(ValidationError, match="over-allocated"):
            check_resource_allocation(worker, t)

    def test_non_overlapping_tasks_do_not_stack(self, project, worker):
        task(
            project, "Earlier", 5, assignee=worker, estimated_hours=Decimal("40"),
            start_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=16), status="In Progress",
        )
        t = task(
            project, "Later", 5, assignee=worker, estimated_hours=Decimal("40"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
        )
        check_resource_allocation(worker, t)

    def test_finished_work_does_not_consume_capacity(self, project, worker):
        task(
            project, "Done", 5, assignee=worker, estimated_hours=Decimal("40"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
            status="Done",
        )
        t = task(
            project, "New", 5, assignee=worker, estimated_hours=Decimal("20"),
            start_date=date.today(), due_date=date.today() + timedelta(days=4),
        )
        check_resource_allocation(worker, t)

    def test_unschedulable_task_is_skipped_not_guessed(self, project, worker):
        t = task(project, "No dates", 5, assignee=worker, estimated_hours=Decimal("999"))
        check_resource_allocation(worker, t)  # must not raise
