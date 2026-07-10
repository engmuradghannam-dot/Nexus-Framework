import pytest
from rest_framework.test import APIClient
from apps.core.models import User


@pytest.mark.django_db
def test_login_and_me_flow():
    User.objects.create_superuser(email='e2e@test.com', password='pw12345')
    client = APIClient()
    # login by email
    res = client.post('/api/core/auth/login/', {'email': 'e2e@test.com', 'password': 'pw12345'}, format='json')
    assert res.status_code == 200, res.data
    assert 'token' in res.data
    assert res.data['user']['email'] == 'e2e@test.com'
    token = res.data['token']
    # use token to hit /me
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    me = client.get('/api/core/users/me/')
    assert me.status_code == 200, me.data
    assert me.data['email'] == 'e2e@test.com'
    # bad password
    bad = client.post('/api/core/auth/login/', {'email': 'e2e@test.com', 'password': 'wrong'}, format='json')
    assert bad.status_code == 401
