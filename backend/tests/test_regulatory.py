import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.core.models import User
from apps.regulatory.models import RegulatoryFramework, ComplianceRule


@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_superuser(
        email='reg@test.com',
        password='testpass123'
    )
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestRegulatory:
    def test_list_frameworks(self, auth_client):
        url = reverse('regulatory:framework-list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_create_framework(self, auth_client):
        url = reverse('regulatory:framework-list')
        data = {
            'name': 'GDPR',
            'description': 'General Data Protection Regulation',
            'jurisdiction': 'EU',
            'compliance_rate': 95.0
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert RegulatoryFramework.objects.count() == 1

    def test_create_rule(self, auth_client):
        framework = RegulatoryFramework.objects.create(
            name='Test Framework',
            jurisdiction='US'
        )
        url = reverse('regulatory:rule-list')
        data = {
            'name': 'Data Retention',
            'description': 'Must retain data for 7 years',
            'framework': framework.id,
            'is_active': True
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert ComplianceRule.objects.count() == 1
