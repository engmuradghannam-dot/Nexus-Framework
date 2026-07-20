import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from nexus.apps.core.models import Company, Branch, Warehouse

@pytest.fixture
def user():
    return User.objects.create_user('testuser', 'test@test.com', 'testpass')

@pytest.fixture
def company():
    return Company.objects.create(name='Test Company')

@pytest.mark.django_db
def test_create_company(company):
    assert company.name == 'Test Company'

@pytest.mark.django_db
def test_create_branch(company):
    branch = Branch.objects.create(company=company, name='Main Branch')
    assert branch.company == company
    assert branch.name == 'Main Branch'

@pytest.mark.django_db
def test_create_warehouse(company):
    branch = Branch.objects.create(company=company, name='Main Branch')
    warehouse = Warehouse.objects.create(branch=branch, name='Main Warehouse', code='WH001')
    assert warehouse.branch == branch
    assert warehouse.is_main == False


@pytest.mark.django_db
def test_regular_user_cannot_create_company(user):
    # Company is the top of the scoping hierarchy every other model is
    # partitioned by - creating one isn't scoped by anything, so it needs
    # its own gate rather than falling through to "any authenticated user".
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post('/api/core/companies/', {'name': 'Shadow Co'}, format='json')
    assert resp.status_code == 403
    assert not Company.objects.filter(name='Shadow Co').exists()


@pytest.mark.django_db
def test_staff_user_can_create_company(user):
    user.is_staff = True
    user.save(update_fields=['is_staff'])
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post('/api/core/companies/', {'name': 'Legit Co'}, format='json')
    assert resp.status_code == 201
    assert Company.objects.filter(name='Legit Co').exists()
