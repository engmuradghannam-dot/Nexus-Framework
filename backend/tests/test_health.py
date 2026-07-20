import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_reports_healthy():
    client = APIClient()
    resp = client.get('/health/', secure=True)
    assert resp.status_code == 200
    assert resp.data['status'] == 'healthy'
    assert resp.data['checks']['database'] == 'ok'


@pytest.mark.django_db
def test_health_check_requires_no_auth():
    # Load balancers / uptime monitors can't log in - this must be reachable
    # unauthenticated, unlike virtually every other endpoint in this project.
    client = APIClient()
    resp = client.get('/health/', secure=True)
    assert resp.status_code in (200, 503)
