"""Stock entries must carry a positive quantity.

StockEntry.quantity had no floor, so the API accepted a "Receipt" of -100 and
drove stock to -100 (HTTP 201). Direction belongs to entry_type — Receipt adds,
Issue removes — never to the sign of the quantity. A negative Receipt subtracts
stock while reading as an addition, and every downstream count assumes stock is
non-negative.
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Floor Co", code="FLR-CO")


@pytest.fixture
def auth_client(db, django_user_model, company):
    u = django_user_model.objects.create_superuser(email="floor@x.com", password="x")
    company.super_admin = u
    company.save(update_fields=["super_admin"])
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.fixture
def warehouse(company):
    branch = Branch.objects.create(company=company, name="Main", code="FLR-MB", address="Riyadh")
    return Warehouse.objects.get(branch=branch)


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="F-1", item_name="Thing")


@pytest.mark.django_db
class TestQuantityFloor:
    def test_api_rejects_a_negative_receipt(self, auth_client, company, warehouse, item):
        r = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "-100", "rate": "1",
        }, format="json")
        assert r.status_code == 400
        assert "quantity" in r.data

    def test_api_rejects_a_zero_quantity(self, auth_client, company, warehouse, item):
        r = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "0", "rate": "1",
        }, format="json")
        assert r.status_code == 400

    def test_api_accepts_a_positive_receipt(self, auth_client, company, warehouse, item):
        r = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "100", "rate": "1",
        }, format="json")
        assert r.status_code == 201
        assert item.stock_in_warehouse(warehouse) == Decimal("100.00")

    def test_removal_uses_issue_not_a_negative_quantity(
        self, auth_client, company, warehouse, item
    ):
        auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Receipt", "quantity": "100", "rate": "1",
        }, format="json")
        r = auth_client.post("/api/inventory/stock-entries/", {
            "company": company.pk, "warehouse": warehouse.pk, "item": item.pk,
            "entry_type": "Issue", "quantity": "30", "rate": "1",
        }, format="json")
        assert r.status_code == 201
        assert item.stock_in_warehouse(warehouse) == Decimal("70.00")

    def test_model_validator_rejects_negative(self, company, warehouse, item):
        entry = StockEntry(
            company=company, warehouse=warehouse, item=item,
            entry_type="Receipt", quantity=Decimal("-5"), rate=Decimal("1"),
        )
        with pytest.raises(ValidationError):
            entry.full_clean()
