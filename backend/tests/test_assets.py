"""Pytest tests for the Fixed Assets module (apps.assets): depreciation
computation and the asset lifecycle. Previously untested (P1 #4 follow-up).
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import Asset
from apps.core.models import CompanyProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="assets@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Assets Co", code="ASSET-CO")


@pytest.mark.django_db
class TestDepreciation:
    def test_straight_line_after_one_full_year(self, company):
        asset = Asset.objects.create(
            company=company, asset_name="Delivery Van", asset_code="AST-1",
            purchase_date=date.today() - timedelta(days=365),
            purchase_value=Decimal("10000"), salvage_value=Decimal("1000"),
            depreciation_method="Straight Line", depreciation_rate=Decimal("10"),
        )
        # Depreciable base 9000 * 10% * ~1 year ≈ 900
        assert abs(asset.accumulated_depreciation - Decimal("900")) < Decimal("5")

    def test_straight_line_never_exceeds_depreciable_base(self, company):
        asset = Asset.objects.create(
            company=company, asset_name="Old Machine", asset_code="AST-2",
            purchase_date=date.today() - timedelta(days=365 * 50),
            purchase_value=Decimal("10000"), salvage_value=Decimal("1000"),
            depreciation_method="Straight Line", depreciation_rate=Decimal("10"),
        )
        assert asset.accumulated_depreciation == Decimal("9000")
        assert asset.book_value == Decimal("1000")

    def test_no_depreciation_method_returns_zero(self, company):
        asset = Asset.objects.create(
            company=company, asset_name="Land", asset_code="AST-3",
            purchase_date=date.today() - timedelta(days=365),
            purchase_value=Decimal("50000"), depreciation_method="None",
        )
        assert asset.accumulated_depreciation == Decimal("0")
        assert asset.book_value == Decimal("50000")

    def test_book_value_is_purchase_minus_accumulated(self, company):
        asset = Asset.objects.create(
            company=company, asset_name="Laptop", asset_code="AST-4",
            purchase_date=date.today() - timedelta(days=365),
            purchase_value=Decimal("4000"), salvage_value=Decimal("0"),
            depreciation_method="Straight Line", depreciation_rate=Decimal("25"),
        )
        assert asset.book_value == asset.purchase_value - asset.accumulated_depreciation


@pytest.mark.django_db
class TestAssetAPI:
    def test_salvage_value_exceeding_purchase_value_rejected(self, auth_client, company):
        response = auth_client.post(
            "/api/assets/assets/",
            {
                "company": str(company.id), "asset_name": "Bad Asset", "asset_code": "AST-BAD",
                "purchase_value": "1000", "salvage_value": "2000",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_then_dispose_transition(self, auth_client, company):
        asset = Asset.objects.create(
            company=company, asset_name="Printer", asset_code="AST-5",
            purchase_value=Decimal("500"), status="Draft",
        )
        r1 = auth_client.patch(f"/api/assets/assets/{asset.id}/", {"status": "Submitted"})
        assert r1.status_code == status.HTTP_200_OK
        r2 = auth_client.patch(f"/api/assets/assets/{asset.id}/", {"status": "Disposed"})
        assert r2.status_code == status.HTTP_200_OK

    def test_invalid_transition_rejected(self, auth_client, company):
        asset = Asset.objects.create(
            company=company, asset_name="Chair", asset_code="AST-6",
            purchase_value=Decimal("200"), status="Draft",
        )
        response = auth_client.patch(f"/api/assets/assets/{asset.id}/", {"status": "Disposed"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_asset_without_company_auto_assigns_the_sole_company(self, auth_client, company):
        response = auth_client.post(
            "/api/assets/assets/",
            {"asset_name": "Auto Co Asset", "asset_code": "AST-AUTO", "purchase_value": "100"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["company"]) == str(company.id)

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/assets/assets/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
