import datetime

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import User
from apps.regulatory.models import Regulation


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
