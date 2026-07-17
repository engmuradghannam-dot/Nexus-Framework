"""Tests for Project.progress auto-calculation from task completion.

Previously Project.progress was a manually-typed field with no real logic
behind it -- the Task-change signal handlers existed in apps/pmo/signals.py
but were empty no-ops, so progress never actually reflected task state.
"""
import pytest

from apps.pmo.models import Project, Task


@pytest.fixture
def project():
    return Project.objects.create(name="Progress Co", status="active")


@pytest.mark.django_db
class TestProjectProgressAutoCalc:
    def test_progress_recomputes_when_a_task_is_marked_done(self, project):
        t1 = Task.objects.create(project=project, title="T1", status="done")
        Task.objects.create(project=project, title="T2", status="todo")
        project.refresh_from_db()
        assert project.progress == 50

    def test_progress_ignores_cancelled_tasks(self, project):
        Task.objects.create(project=project, title="T1", status="done")
        Task.objects.create(project=project, title="T2", status="cancelled")
        project.refresh_from_db()
        assert project.progress == 100

    def test_progress_recomputes_on_task_delete(self, project):
        Task.objects.create(project=project, title="T1", status="done")
        t2 = Task.objects.create(project=project, title="T2", status="todo")
        project.refresh_from_db()
        assert project.progress == 50
        t2.delete()
        project.refresh_from_db()
        assert project.progress == 100

    def test_progress_untouched_when_project_has_no_tasks(self, project):
        project.progress = 42
        project.save()
        project.refresh_from_db()
        assert project.progress == 42

    def test_subtasks_and_priority_and_milestone_link(self, project):
        from apps.pmo.models import Milestone

        milestone = Milestone.objects.create(project=project, name="M1")
        parent = Task.objects.create(project=project, title="Parent", priority="high")
        child = Task.objects.create(
            project=project, title="Child", parent_task=parent, milestone=milestone
        )
        assert parent.subtasks.count() == 1
        assert child.parent_task == parent
        assert child.milestone == milestone
        assert parent.priority == "high"
