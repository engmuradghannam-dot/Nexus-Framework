import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.core.models import User
from apps.pmo.models import Portfolio, Program, Project


@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_superuser(
        email='pmo@test.com',
        password='testpass123'
    )
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestPMOAPI:
    def test_list_portfolios(self, auth_client):
        url = reverse('pmo:portfolio-list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_create_portfolio(self, auth_client):
        url = reverse('pmo:portfolio-list')
        data = {
            'name': 'Test Portfolio',
            'description': 'Test description',
            'status': 'active'
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert Portfolio.objects.count() == 1

    def test_create_project(self, auth_client):
        portfolio = Portfolio.objects.create(name='Test Portfolio', status='active')
        url = reverse('pmo:project-list')
        data = {
            'name': 'Test Project',
            'description': 'Test project',
            'status': 'active',
            'portfolio': portfolio.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert Project.objects.count() == 1
