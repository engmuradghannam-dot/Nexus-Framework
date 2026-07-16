import pytest
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.core.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAuditLogScoping:
    def test_regular_user_only_sees_own_audit_log(self, api_client):
        actor = User.objects.create_user(
            username="actor", email="actor@x.com", password="pw12345678"
        )
        other = User.objects.create_user(
            username="watcher", email="watcher@x.com", password="pw12345678"
        )
        AuditLog.objects.create(
            user=actor, user_email=actor.email, action="update",
            module="hr", object_ref="Employee:1", changes={"salary": 9999},
        )

        api_client.force_authenticate(user=other)
        res = api_client.get("/api/audit/logs/")
        assert res.status_code == 200
        assert res.data["count"] == 0

        api_client.force_authenticate(user=actor)
        res = api_client.get("/api/audit/logs/")
        assert res.data["count"] == 1

    def test_superuser_sees_all_audit_logs(self, api_client):
        actor = User.objects.create_user(
            username="actor2", email="actor2@x.com", password="pw12345678"
        )
        admin = User.objects.create_superuser(
            username="admin6", email="admin6@x.com", password="pw12345678"
        )
        AuditLog.objects.create(
            user=actor, user_email=actor.email, action="create", module="crm",
        )

        api_client.force_authenticate(user=admin)
        res = api_client.get("/api/audit/logs/")
        assert res.status_code == 200
        assert res.data["count"] == 1
