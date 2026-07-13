"""Pytest tests for the Inventory module (apps.inventory): item stock
quantity derivation and the Issue-quantity guard on StockEntry. Previously
untested (P1 #4 follow-up).
"""
from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="inventory@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Inventory Co", code="INV-CO-2")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Depot", code="DEPOT", address="Jubail")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.create(branch=branch, name="Depot WH", code="DWH")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="SKU-INV-1", item_name="Cable Reel", standard_rate=15)


@pytest.mark.django_db
class TestStockQuantity:
    def test_stock_quantity_is_zero_with_no_movements(self, item):
        assert item.stock_quantity == 0

    def test_receipts_increase_and_issues_decrease(self, company, branch, warehouse, item):
        StockEntry.objects.create(company=company, branch=branch, warehouse=warehouse, item=item, entry_type="Receipt", quantity=50, rate=15)
        StockEntry.objects.create(company=company, branch=branch, warehouse=warehouse, item=item, entry_type="Issue", quantity=20, rate=15)
        assert item.stock_quantity == 30


@pytest.mark.django_db
class TestStockEntryAPI:
    def test_receipt_does_not_require_existing_stock(self, auth_client, company, warehouse, item):
        response = auth_client.post(
            "/api/inventory/stock-entries/",
            {"company": str(company.id), "warehouse": str(warehouse.id), "item": item.id, "entry_type": "Receipt", "quantity": "10", "rate": "15"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_issue_beyond_available_stock_rejected(self, auth_client, company, branch, warehouse, item):
        StockEntry.objects.create(company=company, branch=branch, warehouse=warehouse, item=item, entry_type="Receipt", quantity=5, rate=15)
        response = auth_client.post(
            "/api/inventory/stock-entries/",
            {"company": str(company.id), "warehouse": str(warehouse.id), "item": item.id, "entry_type": "Issue", "quantity": "9", "rate": "15"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_issue_within_available_stock_succeeds(self, auth_client, company, branch, warehouse, item):
        StockEntry.objects.create(company=company, branch=branch, warehouse=warehouse, item=item, entry_type="Receipt", quantity=5, rate=15)
        response = auth_client.post(
            "/api/inventory/stock-entries/",
            {"company": str(company.id), "warehouse": str(warehouse.id), "item": item.id, "entry_type": "Issue", "quantity": "5", "rate": "15"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_item_without_company_auto_assigns_the_sole_company(self, auth_client, company):
        response = auth_client.post(
            "/api/inventory/items/",
            {"item_code": "SKU-INV-AUTO", "item_name": "Auto-assigned Item"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["company"]) == str(company.id)

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/inventory/items/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
