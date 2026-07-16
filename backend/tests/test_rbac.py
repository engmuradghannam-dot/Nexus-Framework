import pytest
from rest_framework.test import APIClient

from apps.core.models import User
from apps.rbac.models import Role, RoleAssignment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestRoleSelfEscalation:
    def test_regular_user_cannot_grant_self_a_role(self, api_client):
        role = Role.objects.create(name="Admin", permissions={"accounting": ["view", "delete"]})
        user = User.objects.create_user(
            username="climber", email="climber@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=user)
        res = api_client.post(
            "/api/rbac/assignments/", {"user": str(user.id), "role": role.id}
        )
        assert res.status_code == 403
        assert not RoleAssignment.objects.filter(user=user, role=role).exists()

    def test_regular_user_cannot_edit_role_permissions(self, api_client):
        role = Role.objects.create(name="Viewer", permissions={"accounting": ["view"]})
        user = User.objects.create_user(
            username="editor", email="editor@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=user)
        res = api_client.patch(
            f"/api/rbac/roles/{role.id}/",
            {"permissions": {"accounting": ["view", "delete"]}},
            format="json",
        )
        assert res.status_code == 403
        role.refresh_from_db()
        assert role.permissions == {"accounting": ["view"]}

    def test_regular_user_only_sees_own_assignments(self, api_client):
        role = Role.objects.create(name="Editor")
        user_a = User.objects.create_user(
            username="usera", email="usera@x.com", password="pw12345678"
        )
        user_b = User.objects.create_user(
            username="userb", email="userb@x.com", password="pw12345678"
        )
        RoleAssignment.objects.create(user=user_a, role=role)
        RoleAssignment.objects.create(user=user_b, role=role)

        api_client.force_authenticate(user=user_a)
        res = api_client.get("/api/rbac/assignments/")
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_superuser_can_grant_roles(self, api_client):
        role = Role.objects.create(name="Admin")
        admin = User.objects.create_superuser(
            username="admin5", email="admin5@x.com", password="pw12345678"
        )
        target = User.objects.create_user(
            username="target2", email="target2@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=admin)
        res = api_client.post(
            "/api/rbac/assignments/", {"user": str(target.id), "role": role.id}
        )
        assert res.status_code == 201
        assert RoleAssignment.objects.filter(user=target, role=role).exists()
