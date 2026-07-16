import pytest
from rest_framework.test import APIClient

from apps.controls.models import CompanySetup, FormControl, Industry, IndustryControl
from apps.core.models import User


@pytest.fixture
def auth_client():
    user = User.objects.create_superuser(email="ctrl@test.com", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestControlsModels:
    def test_create_industry_and_control(self):
        Industry.objects.create(code="AVI", name="Aviation", category="Transportation")
        IndustryControl.objects.create(
            industry="Aviation", control_id="AVI-001", control_name="Flight Planning"
        )
        assert Industry.objects.count() == 1
        assert IndustryControl.objects.get(control_id="AVI-001").control_name == (
            "Flight Planning"
        )


@pytest.mark.django_db
class TestControlsAPI:
    def test_list_endpoints(self, auth_client):
        for ep in [
            "industries",
            "industry-controls",
            "ai-agents",
            "master-entities",
            "form-controls",
        ]:
            assert auth_client.get(f"/api/controls/{ep}/").status_code == 200

    def test_summary(self, auth_client):
        FormControl.objects.create(
            form_name="Employee", input_name="ID", status="present", priority="High"
        )
        FormControl.objects.create(
            form_name="Employee", input_name="Phone", status="missing", priority="High"
        )
        res = auth_client.get("/api/controls/form-controls/summary/")
        assert res.status_code == 200
        assert res.data["total"] == 2
        assert res.data["present"] == 1
        assert res.data["coverage_percent"] == 50.0


@pytest.mark.django_db
class TestCompanySetupScoping:
    def test_user_cannot_see_other_users_company_setup(self):
        owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="pw12345678"
        )
        other = User.objects.create_user(
            username="other", email="other@test.com", password="pw12345678"
        )
        CompanySetup.objects.create(
            company_name="Secret Co",
            company_code="SEC1",
            tax_number="TAX-SECRET",
            created_by=owner,
        )

        other_client = APIClient()
        other_client.force_authenticate(user=other)
        res = other_client.get("/api/controls/company-setup/")
        assert res.status_code == 200
        assert res.data["count"] == 0

        owner_client = APIClient()
        owner_client.force_authenticate(user=owner)
        res = owner_client.get("/api/controls/company-setup/")
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_create_sets_owner_automatically(self):
        user = User.objects.create_user(
            username="creator", email="creator@test.com", password="pw12345678"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        res = client.post(
            "/api/controls/company-setup/",
            {"company_name": "New Co", "company_code": "NEW1"},
            format="json",
        )
        assert res.status_code == 201
        setup = CompanySetup.objects.get(company_code="NEW1")
        assert setup.created_by_id == user.id

    def test_superuser_sees_all(self):
        owner = User.objects.create_user(
            username="owner2", email="owner2@test.com", password="pw12345678"
        )
        admin = User.objects.create_superuser(
            username="admin3", email="admin3@test.com", password="pw12345678"
        )
        CompanySetup.objects.create(
            company_name="Secret Co 2", company_code="SEC2", created_by=owner
        )
        client = APIClient()
        client.force_authenticate(user=admin)
        res = client.get("/api/controls/company-setup/")
        assert res.status_code == 200
        assert res.data["count"] == 1
