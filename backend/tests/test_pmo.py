import pytest
from nexus.apps.core.models import Company
from nexus.apps.pmo.models import Project, Task, Milestone

@pytest.fixture
def company():
    return Company.objects.create(name='Test Company')

@pytest.mark.django_db
def test_create_project(company):
    project = Project.objects.create(
        company=company,
        name='Test Project',
        status='planning'
    )
    assert project.name == 'Test Project'
    assert project.status == 'planning'

@pytest.mark.django_db
def test_create_task(company):
    project = Project.objects.create(company=company, name='Test Project')
    task = Task.objects.create(
        project=project,
        title='Test Task',
        priority='high'
    )
    assert task.project == project
    assert task.priority == 'high'
    assert task.completed == False
