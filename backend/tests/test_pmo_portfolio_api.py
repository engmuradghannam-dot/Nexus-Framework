import pytest
from rest_framework.test import APIClient
from apps.core.models import User
from apps.pmo.models import Portfolio


@pytest.mark.django_db
def test_portfolio_list_and_create():
    User.objects.create_superuser(email='pf@test.com', password='pw12345')
    client = APIClient()
    client.force_authenticate(user=User.objects.get(email='pf@test.com'))
    assert client.get('/api/pmo/portfolios/').status_code == 200
    res = client.post('/api/pmo/portfolios/', {'name': 'Digital', 'status': 'active'}, format='json')
    assert res.status_code == 201, res.data
    assert Portfolio.objects.filter(name='Digital').count() == 1
