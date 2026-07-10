import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import User
from apps.pmo.models import Milestone, Portfolio, Project, Task


@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_superuser(
        email="pmo@test.com",
        password="testpass123",
    )
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestPMOModels:
    def test_create_portfolio(self):
        portfolio = Portfolio.objects.create(name="Test Portfolio", status="active")
        assert portfolio.name == "Test Portfolio"
        assert Portfolio.objects.count() == 1

    def test_create_project_with_portfolio(self):
        portfolio = Portfolio.objects.create(name="Test Portfolio", status="active")
        project = Project.objects.create(
            name="Test Project", portfolio=portfolio, status="active"
        )
        assert project.portfolio == portfolio
        assert project.budget_utilization == 0

    def test_task_and_milestone(self):
        project = Project.objects.create(name="P", status="planning")
        task = Task.objects.create(project=project, title="T", status="todo")
        milestone = Milestone.objects.create(project=project, name="M1")
        assert task.project == project
        assert milestone.is_achieved is False


@pytest.mark.django_db
class TestPMOAPI:
    def test_list_projects(self, auth_client):
        response = auth_client.get(reverse("project-list"))
        assert response.status_code == 200

    def test_create_project(self, auth_client):
        response = auth_client.post(
            reverse("project-list"),
            {"name": "API Project", "status": "active"},
        )
        assert response.status_code == 201
        assert Project.objects.count() == 1

    def test_list_tasks(self, auth_client):
        assert auth_client.get(reverse("task-list")).status_code == 200

    def test_list_milestones(self, auth_client):
        assert auth_client.get(reverse("milestone-list")).status_code == 200
