import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.ai_module.models import AIModel
from apps.core.models import User


@pytest.fixture
def user():
    return User.objects.create_superuser(
        email="ai@test.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAIModuleModels:
    def test_create_ai_model(self, user):
        model = AIModel.objects.create(
            name="Sales Forecaster",
            version="1.0.0",
            model_type=AIModel._meta.get_field("model_type").choices[0][0],
            owner=user,
        )
        assert model.name == "Sales Forecaster"
        assert AIModel.objects.count() == 1


@pytest.mark.django_db
class TestAIModuleAPI:
    def test_list_models(self, auth_client):
        assert auth_client.get(reverse("aimodel-list")).status_code == 200

    def test_list_predictions(self, auth_client):
        assert auth_client.get(reverse("prediction-list")).status_code == 200

    def test_list_insights(self, auth_client):
        assert auth_client.get(reverse("insight-list")).status_code == 200
