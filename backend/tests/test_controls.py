import pytest
from rest_framework.test import APIClient

from apps.controls.models import FormControl, Industry, IndustryControl
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
