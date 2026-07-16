import pytest
from django.contrib.auth.models import User
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
