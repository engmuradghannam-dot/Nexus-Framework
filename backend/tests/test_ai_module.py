import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.core.models import User
from apps.ai_module.models import AIModel, AIInsight


@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_superuser(
        email='ai@test.com',
        password='testpass123'
    )
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAIModule:
    def test_create_model(self, auth_client):
        url = reverse('ai_module:model-list')
        data = {
            'name': 'Risk Predictor',
            'model_type': 'classification',
            'version': '1.0.0',
            'accuracy': 0.95,
            'is_active': True
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert AIModel.objects.count() == 1

    def test_create_insight(self, auth_client):
        model = AIModel.objects.create(
            name='Test Model',
            model_type='regression',
            version='1.0'
        )
        url = reverse('ai_module:insight-list')
        data = {
            'title': 'Test Insight',
            'description': 'This is a test insight',
            'insight_type': 'prediction',
            'confidence_score': 0.85,
            'model': model.id
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201
        assert AIInsight.objects.count() == 1
