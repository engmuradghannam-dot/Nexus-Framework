import pytest
from django.conf import settings
import os

# Configure Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def company():
    from apps.core.models import Company
    return Company.objects.create(
        name='Test Company',
        tax_id='123456789',
        email='company@test.com'
    )
