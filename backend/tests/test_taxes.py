"""Comprehensive Pytest tests for Taxes APIs."""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.taxes.models import CountryTaxProfile, TaxRate, TaxRule


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="test@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def sa_profile():
    return CountryTaxProfile.objects.create(
        country_code="SA",
        country_name="Saudi Arabia",
        currency_code="SAR",
        vat_enabled=True,
        vat_standard_rate=15.00,
        sales_tax_enabled=False,
        withholding_tax_enabled=True,
        withholding_tax_rate=2.50,
    )


@pytest.fixture
def us_profile():
    return CountryTaxProfile.objects.create(
        country_code="US",
        country_name="United States",
        currency_code="USD",
        vat_enabled=False,
        sales_tax_enabled=True,
        sales_tax_rate=7.25,
    )


@pytest.mark.django_db
class TestCountryTaxProfileAPI:
    def test_list_profiles(self, auth_client):
        CountryTaxProfile.objects.create(
            country_code="GB",
            country_name="United Kingdom",
            currency_code="GBP",
            vat_enabled=True,
            vat_standard_rate=20.00,
        )
        response = auth_client.get("/api/taxes/profiles/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_profile(self, auth_client):
        data = {
            "country_code": "FR",
            "country_name": "France",
            "currency_code": "EUR",
            "vat_enabled": True,
            "vat_standard_rate": "20.00",
        }
        response = auth_client.post("/api/taxes/profiles/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["country_code"] == "FR"

    def test_retrieve_profile(self, auth_client, sa_profile):
        response = auth_client.get(f"/api/taxes/profiles/{sa_profile.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["country_code"] == "SA"
        assert response.data["vat_standard_rate"] == "15.00"

    def test_update_profile(self, auth_client, sa_profile):
        data = {"vat_standard_rate": "20.00"}
        response = auth_client.patch(f"/api/taxes/profiles/{sa_profile.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        sa_profile.refresh_from_db()
        assert str(sa_profile.vat_standard_rate) == "20.00"

    def test_delete_profile(self, auth_client, sa_profile):
        response = auth_client.delete(f"/api/taxes/profiles/{sa_profile.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CountryTaxProfile.objects.filter(id=sa_profile.id).exists()

    def test_by_code_action(self, auth_client, sa_profile):
        response = auth_client.get("/api/taxes/profiles/by-code/SA/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["country_code"] == "SA"

    def test_unauthenticated_access(self, api_client):
        response = api_client.get("/api/taxes/profiles/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTaxRateAPI:
    def test_list_rates(self, auth_client, sa_profile):
        TaxRate.objects.create(country=sa_profile, name="VAT", tax_type="vat_standard", rate=15.00)
        response = auth_client.get("/api/taxes/rates/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_rate(self, auth_client, sa_profile):
        data = {
            "country": str(sa_profile.id),
            "name": "Reduced VAT",
            "tax_type": "vat_reduced",
            "rate": "5.00",
        }
        response = auth_client.post("/api/taxes/rates/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_by_country(self, auth_client, sa_profile, us_profile):
        TaxRate.objects.create(country=sa_profile, name="VAT", tax_type="vat_standard", rate=15.00)
        TaxRate.objects.create(country=us_profile, name="Sales Tax", tax_type="sales", rate=7.25)
        response = auth_client.get(f"/api/taxes/rates/?country={sa_profile.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestTaxRuleAPI:
    def test_list_rules(self, auth_client, sa_profile):
        TaxRule.objects.create(
            country=sa_profile,
            name="B2B Zero",
            rule_type="exemption",
            conditions={"is_b2b": True},
        )
        response = auth_client.get("/api/taxes/rules/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_rule(self, auth_client, sa_profile):
        data = {
            "country": str(sa_profile.id),
            "name": "Export Rule",
            "rule_type": "exemption",
            "conditions": {"export": True},
            "priority": 5,
        }
        response = auth_client.post("/api/taxes/rules/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestTaxCalculationAPI:
    def test_calculate_tax(self, auth_client, sa_profile):
        data = {
            "country": str(sa_profile.id),
            "reference_number": "INV-001",
            "base_amount": "1000.00",
            "is_b2b": False,
        }
        response = auth_client.post("/api/taxes/calculations/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "tax_amount" in response.data
        assert "total_amount" in response.data

    def test_calculator_action(self, auth_client, sa_profile):
        data = {
            "country_code": "SA",
            "amount": "1000.00",
            "is_b2b": False,
        }
        response = auth_client.post("/api/taxes/calculations/calculate/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["country_code"] == "SA"
        assert float(response.data["tax_amount"]) > 0

    def test_b2b_zero_rate(self, auth_client, sa_profile):
        TaxRule.objects.create(
            country=sa_profile,
            name="B2B Zero",
            rule_type="exemption",
            conditions={"is_b2b": True, "has_vat_id": True},
            tax_rate_override=0.00,
            is_active=True,
        )
        data = {
            "country": str(sa_profile.id),
            "reference_number": "INV-002",
            "base_amount": "1000.00",
            "is_b2b": True,
            "customer_vat_id": "300000000000003",
        }
        response = auth_client.post("/api/taxes/calculations/", data)
        assert response.status_code == status.HTTP_201_CREATED
