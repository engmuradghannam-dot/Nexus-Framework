import pytest
from rest_framework.test import APIClient
from apps.core.models import User
from apps.twofa import totp
from apps.twofa.models import TwoFactor


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


@pytest.mark.django_db
def test_register_creates_account_and_logs_in():
    client = APIClient()
    res = client.post('/api/core/auth/register/', {
        'email': 'newuser@test.com', 'password': 'strongpass123',
        'first_name': 'New', 'last_name': 'User',
    }, format='json')
    assert res.status_code == 201, res.data
    assert 'token' in res.data
    assert res.data['user']['email'] == 'newuser@test.com'
    assert User.objects.filter(email='newuser@test.com').exists()

    # the returned token must actually work
    token = res.data['token']
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    me = client.get('/api/core/users/me/')
    assert me.status_code == 200
    assert me.data['email'] == 'newuser@test.com'


@pytest.mark.django_db
def test_register_rejects_duplicate_email():
    User.objects.create_user(email='dupe@test.com', password='whatever123')
    client = APIClient()
    res = client.post('/api/core/auth/register/', {
        'email': 'dupe@test.com', 'password': 'anotherpass123',
    }, format='json')
    assert res.status_code == 400


def test_register_rejects_short_password():
    client = APIClient()
    res = client.post('/api/core/auth/register/', {
        'email': 'short@test.com', 'password': '123',
    }, format='json')
    assert res.status_code == 400


def test_register_rejects_invalid_email():
    client = APIClient()
    res = client.post('/api/core/auth/register/', {
        'email': 'not-an-email', 'password': 'strongpass123',
    }, format='json')
    assert res.status_code == 400


def test_register_rejects_missing_fields():
    client = APIClient()
    res = client.post('/api/core/auth/register/', {'email': 'nofields@test.com'}, format='json')
    assert res.status_code == 400


@pytest.mark.django_db
class TestTwoFactorLoginEnforcement:
    def test_login_blocked_without_otp_when_2fa_enabled(self):
        user = User.objects.create_user(email='has2fa@test.com', username='has2fa', password='pw12345678')
        TwoFactor.objects.create(user=user, secret=totp.random_base32(), enabled=True)
        client = APIClient()
        res = client.post('/api/core/auth/login/', {'email': 'has2fa@test.com', 'password': 'pw12345678'}, format='json')
        assert res.status_code == 401
        assert res.data.get('two_factor_required') is True

    def test_login_blocked_with_wrong_otp(self):
        user = User.objects.create_user(email='has2fa2@test.com', username='has2fa2', password='pw12345678')
        TwoFactor.objects.create(user=user, secret=totp.random_base32(), enabled=True)
        client = APIClient()
        res = client.post('/api/core/auth/login/', {
            'email': 'has2fa2@test.com', 'password': 'pw12345678', 'otp_code': '000000',
        }, format='json')
        assert res.status_code == 401

    def test_login_succeeds_with_correct_otp(self):
        user = User.objects.create_user(email='has2fa3@test.com', username='has2fa3', password='pw12345678')
        secret = totp.random_base32()
        TwoFactor.objects.create(user=user, secret=secret, enabled=True)
        client = APIClient()
        res = client.post('/api/core/auth/login/', {
            'email': 'has2fa3@test.com', 'password': 'pw12345678', 'otp_code': totp.now_totp(secret),
        }, format='json')
        assert res.status_code == 200
        assert 'token' in res.data

    def test_login_unaffected_when_2fa_not_enabled(self):
        User.objects.create_user(email='no2fa@test.com', username='no2fa', password='pw12345678')
        client = APIClient()
        res = client.post('/api/core/auth/login/', {'email': 'no2fa@test.com', 'password': 'pw12345678'}, format='json')
        assert res.status_code == 200
