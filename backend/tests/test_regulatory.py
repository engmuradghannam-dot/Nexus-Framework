import datetime

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, User
from apps.regulatory.models import ComplianceCheck, Regulation, Risk


@pytest.fixture
def user():
    return User.objects.create_superuser(
        email="reg@test.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestRegulatoryModels:
    def test_create_regulation(self, user):
        reg = Regulation.objects.create(
            title="ZATCA E-Invoicing",
            code="ZATCA-01",
            jurisdiction="SA",
            severity="high",
            effective_date=datetime.date(2024, 1, 1),
            description="E-invoicing compliance requirement.",
            created_by=user,
        )
        assert reg.code == "ZATCA-01"
        assert Regulation.objects.count() == 1


@pytest.mark.django_db
class TestRegulatoryAPI:
    def test_list_regulations(self, auth_client):
        assert auth_client.get(reverse("regulation-list")).status_code == 200

    def test_list_compliance_checks(self, auth_client):
        assert auth_client.get(reverse("compliancecheck-list")).status_code == 200

    def test_list_risks(self, auth_client):
        assert auth_client.get(reverse("risk-list")).status_code == 200


@pytest.mark.django_db
class TestRegulatoryScoping:
    def test_regular_user_only_sees_own_risks(self):
        owner = User.objects.create_user(
            username="riskowner", email="riskowner@x.com", password="pw12345678"
        )
        other = User.objects.create_user(
            username="outsider3", email="outsider3@x.com", password="pw12345678"
        )
        Risk.objects.create(
            title="Confidential risk",
            description="secret mitigation",
            likelihood=3,
            impact=3,
            owner=owner,
        )
        client = APIClient()
        client.force_authenticate(user=other)
        res = client.get(reverse("risk-list"))
        assert res.status_code == 200
        assert res.data["count"] == 0

        client.force_authenticate(user=owner)
        res = client.get(reverse("risk-list"))
        assert res.data["count"] == 1

    def test_regular_user_only_sees_own_company_compliance_checks(self):
        owner = User.objects.create_user(
            username="compowner", email="compowner@x.com", password="pw12345678"
        )
        other = User.objects.create_user(
            username="outsider4", email="outsider4@x.com", password="pw12345678"
        )
        company = CompanyProfile.objects.create(name="Comp Co", code="COMP1", super_admin=owner)
        branch = Branch.objects.create(name="HQ", code="HQ-COMP", address="x", company=company)
        reg = Regulation.objects.create(
            title="ZATCA", code="Z-1", jurisdiction="SA", severity="high",
            effective_date=datetime.date(2024, 1, 1), description="d",
            created_by=owner,
        )
        ComplianceCheck.objects.create(regulation=reg, branch=branch, result="pass")

        client = APIClient()
        client.force_authenticate(user=other)
        res = client.get(reverse("compliancecheck-list"))
        assert res.status_code == 200
        assert res.data["count"] == 0

        client.force_authenticate(user=owner)
        res = client.get(reverse("compliancecheck-list"))
        assert res.data["count"] == 1
