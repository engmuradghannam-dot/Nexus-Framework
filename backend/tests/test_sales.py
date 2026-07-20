from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from nexus.apps.core.models import Branch, Company, Warehouse
from nexus.apps.crm.models import Customer
from nexus.apps.sales.models import SalesOrder


@pytest.fixture
def warehouse():
    company = Company.objects.create(name='Test Company')
    branch = Branch.objects.create(company=company, name='Main Branch')
    return Warehouse.objects.create(branch=branch, name='Main WH', code='WH-SAL-001')


@pytest.fixture
def customer(warehouse):
    return Customer.objects.create(
        customer_name='Retail Co', email='retail@test.com', phone='0500000000',
        branch=warehouse.branch, credit_limit=Decimal('20000'),
    )


@pytest.mark.django_db
def test_so_id_auto_generated(customer, warehouse):
    order = SalesOrder.objects.create(
        customer=customer, warehouse=warehouse, total_amount=1000, shipping_address='123 King Fahd Rd',
    )
    assert order.so_id.startswith('SO-')


@pytest.mark.django_db
def test_discount_exceeding_30_percent_rejected(customer, warehouse):
    # SAL-Inputs validation: discount_amount <= total_amount * 0.30
    order = SalesOrder(
        customer=customer, warehouse=warehouse, total_amount=1000, discount_amount=500,
        shipping_address='123 King Fahd Rd',
    )
    with pytest.raises(ValidationError):
        order.clean()


@pytest.mark.django_db
def test_discount_authorization_threshold(customer, warehouse):
    # SAL-CTRL-004 Discount Authorization (> 10%)
    order = SalesOrder.objects.create(
        customer=customer, warehouse=warehouse, total_amount=1000, discount_amount=150,
        shipping_address='123 King Fahd Rd',
    )
    assert order.requires_discount_approval is True


@pytest.mark.django_db
def test_vat_calculation_on_order(customer, warehouse):
    # SAL-Inputs: tax_amount auto-calculated (15% VAT)
    order = SalesOrder.objects.create(
        customer=customer, warehouse=warehouse, total_amount=1000, discount_amount=0,
        shipping_address='123 King Fahd Rd',
    )
    assert order.calculate_tax() == Decimal('150.00')


@pytest.mark.django_db
def test_credit_check_blocks_over_limit_order(customer, warehouse):
    # SAL-CTRL-001 Credit Check
    order = SalesOrder.objects.create(
        customer=customer, warehouse=warehouse, total_amount=25000, shipping_address='123 King Fahd Rd',
    )
    assert order.check_credit() is False


@pytest.mark.django_db
def test_create_order_via_api_serializes_cleanly(customer, warehouse):
    # order_date used to default to timezone.now() (a datetime) on a
    # DateField - harmless via .objects.create(), but DRF's serializer
    # asserts on representing a raw datetime as a date field and crashed
    # with a 500 on every single order created through the API.
    user = User.objects.create_user('salesuser', 'sales@test.com', 'pass')
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post('/api/sales/orders/', {
        'customer': customer.id, 'warehouse': warehouse.id,
        'shipping_address': '123 King Fahd Rd', 'required_date': '2026-08-01',
    }, format='json', secure=True)

    assert resp.status_code == 201
    assert resp.data['order_date'] is not None
