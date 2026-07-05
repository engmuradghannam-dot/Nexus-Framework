import pytest
from rest_framework.test import APIClient
from apps.core.models import User, Company

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@nexus.com', 
        password='admin123', 
        first_name='Admin', 
        last_name='User'
    )

@pytest.fixture
def company(db):
    return Company.objects.create(name='Test Company', tax_id='123456')

@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
