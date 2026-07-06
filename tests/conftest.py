import pytest
from rest_framework.test import APIClient
from apps.core.models import User, Company, Branch, Warehouse
from apps.buying.models import Supplier
from apps.selling.models import Customer
from apps.inventory.models import Item, ItemGroup
from apps.hr.models import Employee, Team

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
    return Company.objects.create(name='Test Company', tax_id='123456', currency='SAR')

@pytest.fixture
def company2(db):
    return Company.objects.create(name='Rival Company', tax_id='999999', currency='SAR')

@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def branch(db, company):
    return Branch.objects.create(company=company, name='Main Branch')

@pytest.fixture
def warehouse(db, branch):
    return Warehouse.objects.create(branch=branch, name='Main Warehouse', code='WH-TEST')

@pytest.fixture
def supplier(db, company):
    return Supplier.objects.create(company=company, name='Test Supplier')

@pytest.fixture
def customer(db, company):
    return Customer.objects.create(company=company, name='Test Customer')

@pytest.fixture
def item(db, company):
    return Item.objects.create(company=company, item_code='TEST-ITM', item_name='Test Item')

@pytest.fixture
def company_user(db, company):
    """A regular (non-superuser, non-staff) user tied to `company`."""
    return User.objects.create_user(email='user1@nexus.com', password='pass123', company=company)

@pytest.fixture
def company2_user(db, company2):
    """A regular user tied to `company2`, for cross-tenant isolation tests."""
    return User.objects.create_user(email='user2@nexus.com', password='pass123', company=company2)

@pytest.fixture
def company_client(api_client, company_user):
    api_client.force_authenticate(user=company_user)
    return api_client

@pytest.fixture
def company2_client(api_client, company2_user):
    api_client.force_authenticate(user=company2_user)
    return api_client

@pytest.fixture
def employee(db, company, company_user):
    return Employee.objects.create(
        company=company, employee_id='E1', first_name='Sara', last_name='Ali', user=company_user
    )

@pytest.fixture
def employee2(db, company):
    return Employee.objects.create(company=company, employee_id='E2', first_name='Omar', last_name='Nasser')

@pytest.fixture
def team(db, company, employee, employee2):
    t = Team.objects.create(company=company, name='Dev Team')
    t.members.add(employee, employee2)
    return t

