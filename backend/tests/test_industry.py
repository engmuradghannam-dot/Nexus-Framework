import pytest
from nexus.apps.core.models import Company, Branch, Warehouse
from nexus.apps.industry.models import Product, Inventory, Supplier

@pytest.fixture
def warehouse():
    company = Company.objects.create(name='Test Company')
    branch = Branch.objects.create(company=company, name='Main Branch')
    return Warehouse.objects.create(branch=branch, name='Main WH', code='WH001')

@pytest.mark.django_db
def test_create_product():
    product = Product.objects.create(name='Test Product', sku='SKU001')
    assert product.name == 'Test Product'
    assert product.sku == 'SKU001'

@pytest.mark.django_db
def test_inventory_needs_reorder(warehouse):
    product = Product.objects.create(name='Test Product', sku='SKU001')
    inventory = Inventory.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=5,
        min_reorder_level=10
    )
    assert inventory.needs_reorder == True

@pytest.mark.django_db
def test_inventory_no_reorder(warehouse):
    product = Product.objects.create(name='Test Product', sku='SKU001')
    inventory = Inventory.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=20,
        min_reorder_level=10
    )
    assert inventory.needs_reorder == False
