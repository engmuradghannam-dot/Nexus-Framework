import pytest
from apps.pmo.models import Project, Task
from apps.core.models import User


@pytest.mark.django_db
def test_project_budget_utilization():
    user = User.objects.create_user(email='test@test.com', username='test', password='test')
    project = Project.objects.create(
        name='Test Project', code='PRJ-001', owner=user,
        start_date='2026-01-01', end_date='2026-12-31',
        budget=100000, spent=75000
    )
    assert project.budget_utilization == 75.00
