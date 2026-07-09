import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.core.models import User
from apps.industry.models import IndustryProject, IndustryMetric


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def auth_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_project():
    return IndustryProject.objects.create(
        name='Test Project',
        sector='Manufacturing',
        status='active',
        budget=1000000
    )


@pytest.mark.django_db
class TestIndustryAPI:
    def test_list_projects(self, auth_client, sample_project):
        url = reverse('industry:project-list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_create_project(self, auth_client):
        url = reverse('industry:project-list')
        data = {
            'name': 'New Project',
            'sector': 'Energy',
            'status': 'active',
            'budget': 500000
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert IndustryProject.objects.count() == 1

    def test_project_signals(self, auth_client):
        url = reverse('industry:project-list')
        data = {
            'name': 'Signal Test Project',
            'sector': 'Healthcare',
            'status': 'active',
            'budget': 750000
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        project = IndustryProject.objects.first()
        assert IndustryMetric.objects.filter(project=project).exists()


@pytest.mark.django_db
class TestIndustryModels:
    def test_project_str(self, sample_project):
        assert str(sample_project) == 'Test Project'

    def test_metric_creation(self, sample_project):
        metric = IndustryMetric.objects.create(
            project=sample_project,
            efficiency_score=85.5,
            compliance_rate=95.0,
            risk_level='low'
        )
        assert metric.efficiency_score == 85.5
