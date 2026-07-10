"""
Industry API Tests
Tests for Industry Vertical, Company, Sector, Metric, and VerticalTemplate APIs.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import User
from apps.industry.models import (
    Company,
    IndustryVertical,
    Metric,
    Sector,
    VerticalTemplate,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        email="admin@test.com",
        password="testpass123",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def auth_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_vertical(admin_user):
    return IndustryVertical.objects.create(
        name="Manufacturing",
        code="MFG",
        description="Manufacturing industry vertical",
        modules_enabled=["core", "pmo", "industry"],
        features_config={"pmo": ["projects", "tasks"]},
        report_templates=["quarterly_report", "annual_report"],
        default_currency="USD",
        multi_branch_enabled=True,
        multi_warehouse_enabled=True,
        created_by=admin_user,
    )


@pytest.fixture
def sample_template():
    return VerticalTemplate.objects.create(
        name="Manufacturing Template",
        vertical_type="manufacturing",
        description="Default template for manufacturing",
        default_modules=["core", "pmo", "industry"],
        default_features={"pmo": ["projects"]},
        default_reports=["quarterly_report"],
        default_compliance=["ISO9001"],
    )


@pytest.fixture
def sample_company(sample_vertical):
    return Company.objects.create(
        name="Acme Corp",
        ticker="ACME",
        industry_vertical=sample_vertical,
        market_cap=1000000000.00,
        revenue=500000000.00,
        employees=5000,
        headquarters="New York, USA",
        website="https://acme.example.com",
        currency="USD",
        multi_branch_enabled=True,
        multi_warehouse_enabled=True,
    )


@pytest.fixture
def sample_sector(sample_vertical):
    return Sector.objects.create(
        name="Heavy Machinery",
        code="HM",
        industry_vertical=sample_vertical,
        description="Heavy machinery manufacturing sector",
    )


@pytest.fixture
def sample_metric(sample_company):
    return Metric.objects.create(
        company=sample_company,
        name="Revenue Growth",
        metric_type="financial",
        value=15.5,
        unit="percent",
        period="Q1-2026",
    )


# ────────────────────────────────────────────
# IndustryVertical API Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestIndustryVerticalAPI:
    def test_list_verticals(self, auth_client, sample_vertical):
        url = reverse("vertical-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_vertical(self, auth_client):
        url = reverse("vertical-list")
        data = {
            "name": "Healthcare",
            "code": "HLT",
            "description": "Healthcare industry vertical",
            "modules_enabled": ["core", "industry"],
            "features_config": {},
            "default_currency": "USD",
            "multi_branch_enabled": False,
            "multi_warehouse_enabled": False,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201
        assert IndustryVertical.objects.filter(code="HLT").exists()

    def test_vertical_detail(self, auth_client, sample_vertical):
        url = reverse("vertical-detail", kwargs={"pk": str(sample_vertical.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Manufacturing"

    def test_vertical_modules_action(self, auth_client, sample_vertical):
        url = reverse("vertical-modules", kwargs={"pk": str(sample_vertical.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert "modules_enabled" in response.data

    def test_vertical_companies_action(
        self, auth_client, sample_vertical, sample_company
    ):
        url = reverse("vertical-companies", kwargs={"pk": str(sample_vertical.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_active_verticals_action(self, auth_client, sample_vertical):
        url = reverse("vertical-active-verticals")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_clone_from_template(self, auth_client, sample_vertical, sample_template):
        url = reverse(
            "vertical-clone-from-template", kwargs={"pk": str(sample_vertical.id)}
        )
        response = auth_client.post(
            url, {"template_id": str(sample_template.id)}, format="json"
        )
        assert response.status_code == 200
        sample_vertical.refresh_from_db()
        assert sample_vertical.modules_enabled == ["core", "pmo", "industry"]


# ────────────────────────────────────────────
# VerticalTemplate API Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestVerticalTemplateAPI:
    def test_list_templates(self, auth_client, sample_template):
        url = reverse("template-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_template_detail(self, auth_client, sample_template):
        url = reverse("template-detail", kwargs={"pk": str(sample_template.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Manufacturing Template"

    def test_template_preview(self, auth_client, sample_template):
        url = reverse("template-preview", kwargs={"pk": str(sample_template.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert "modules" in response.data


# ────────────────────────────────────────────
# Company API Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestCompanyAPI:
    def test_list_companies(self, auth_client, sample_company):
        url = reverse("company-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_company(self, auth_client, sample_vertical):
        url = reverse("company-list")
        data = {
            "name": "Beta Inc",
            "ticker": "BETA",
            "industry_vertical": str(sample_vertical.id),
            "market_cap": 500000000.00,
            "revenue": 250000000.00,
            "employees": 2000,
            "headquarters": "London, UK",
            "currency": "GBP",
            "multi_branch_enabled": False,
            "multi_warehouse_enabled": False,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201
        assert Company.objects.filter(ticker="BETA").exists()

    def test_company_detail(self, auth_client, sample_company):
        url = reverse("company-detail", kwargs={"pk": str(sample_company.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Acme Corp"

    def test_company_modules_action(self, auth_client, sample_company):
        url = reverse("company-modules", kwargs={"pk": str(sample_company.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert "effective_modules" in response.data

    def test_company_reports_action(self, auth_client, sample_company):
        url = reverse("company-reports", kwargs={"pk": str(sample_company.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert "available_reports" in response.data

    def test_company_metrics_action(self, auth_client, sample_company, sample_metric):
        url = reverse("company-metrics", kwargs={"pk": str(sample_company.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        # A company is seeded with an 'initial' metric on creation, plus the
        # sample metric created by the fixture.
        names = [m["name"] for m in response.data]
        assert "Revenue Growth" in names
        assert len(response.data) >= 1

    def test_company_by_vertical(self, auth_client, sample_vertical, sample_company):
        url = reverse("company-by-vertical")
        response = auth_client.get(url, {"vertical_id": str(sample_vertical.id)})
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_company_leaderboard(self, auth_client, sample_company):
        url = reverse("company-leaderboard")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1


# ────────────────────────────────────────────
# Sector API Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestSectorAPI:
    def test_list_sectors(self, auth_client, sample_sector):
        url = reverse("sector-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_sector(self, auth_client, sample_vertical):
        url = reverse("sector-list")
        data = {
            "name": "Automotive",
            "code": "AUTO",
            "industry_vertical": str(sample_vertical.id),
            "description": "Automotive manufacturing",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201
        assert Sector.objects.filter(code="AUTO").exists()

    def test_sector_detail(self, auth_client, sample_sector):
        url = reverse("sector-detail", kwargs={"pk": str(sample_sector.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Heavy Machinery"


# ────────────────────────────────────────────
# Metric API Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestMetricAPI:
    def test_list_metrics(self, auth_client, sample_metric):
        url = reverse("metric-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_metric(self, auth_client, sample_company):
        url = reverse("metric-list")
        data = {
            "company": str(sample_company.id),
            "name": "Employee Satisfaction",
            "metric_type": "operational",
            "value": 87.5,
            "unit": "score",
            "period": "Q2-2026",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201
        assert Metric.objects.filter(name="Employee Satisfaction").exists()

    def test_metric_detail(self, auth_client, sample_metric):
        url = reverse("metric-detail", kwargs={"pk": str(sample_metric.id)})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Revenue Growth"


# ────────────────────────────────────────────
# Model Tests
# ────────────────────────────────────────────
@pytest.mark.django_db
class TestIndustryModels:
    def test_vertical_str(self, sample_vertical):
        assert str(sample_vertical) == "Manufacturing (MFG)"

    def test_vertical_module_count(self, sample_vertical):
        assert sample_vertical.module_count == 3

    def test_vertical_feature_count(self, sample_vertical):
        assert sample_vertical.feature_count == 2

    def test_template_str(self, sample_template):
        assert str(sample_template) == "Manufacturing Template (manufacturing)"

    def test_company_str(self, sample_company):
        assert "Acme Corp" in str(sample_company)
        assert "Manufacturing" in str(sample_company)

    def test_company_effective_modules(self, sample_company, sample_vertical):
        assert "core" in sample_company.effective_modules
        assert "pmo" in sample_company.effective_modules

    def test_company_effective_features(self, sample_company):
        assert "pmo" in sample_company.effective_features

    def test_company_available_reports(self, sample_company):
        assert "quarterly_report" in sample_company.available_reports

    def test_sector_str(self, sample_sector):
        assert "Heavy Machinery" in str(sample_sector)

    def test_metric_str(self, sample_metric):
        assert "Acme Corp" in str(sample_metric)
        assert "Revenue Growth" in str(sample_metric)
