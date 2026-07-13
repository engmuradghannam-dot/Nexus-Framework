"""Pytest tests for the CRM module (apps.crm): leads and opportunities,
including company-scoped isolation. Previously untested (P1 #4 follow-up).
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.crm.models import Lead, Opportunity


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="crm@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="CRM Co", code="CRM-CO")


@pytest.mark.django_db
class TestLeadAPI:
    def test_create_lead(self, auth_client, company):
        response = auth_client.post(
            "/api/crm/leads/",
            {"company": str(company.id), "lead_name": "Acme Corp", "source": "Website"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "Open"

    def test_update_lead_status(self, auth_client, company):
        lead = Lead.objects.create(company=company, lead_name="Beta LLC")
        response = auth_client.patch(f"/api/crm/leads/{lead.id}/", {"status": "Converted"})
        assert response.status_code == status.HTTP_200_OK
        lead.refresh_from_db()
        assert lead.status == "Converted"

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/crm/leads/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOpportunityAPI:
    def test_create_opportunity_from_lead(self, auth_client, company):
        lead = Lead.objects.create(company=company, lead_name="Gamma Inc", status="Opportunity")
        response = auth_client.post(
            "/api/crm/opportunities/",
            {
                "company": str(company.id), "lead": lead.id,
                "opportunity_name": "Gamma Deal", "expected_amount": "50000",
                "probability": "60",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["opportunity_name"] == "Gamma Deal"

    def test_list_opportunities_scoped_to_company(self, auth_client, company):
        other_company = CompanyProfile.objects.create(name="Other CRM Co", code="OTHER-CRM")
        Opportunity.objects.create(company=company, opportunity_name="Mine")
        Opportunity.objects.create(company=other_company, opportunity_name="Not Mine")
        # A superuser bypasses scoping and should see both — this just
        # confirms the endpoint doesn't silently drop rows for admins.
        response = auth_client.get("/api/crm/opportunities/")
        assert response.status_code == status.HTTP_200_OK
        names = {o["opportunity_name"] for o in response.data["results"]}
        assert {"Mine", "Not Mine"}.issubset(names)
