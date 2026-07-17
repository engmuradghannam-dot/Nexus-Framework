"""Tests for apps.rbac.RoleViewSet.

Two separate protections live here:
- self-escalation: a regular user must not be able to grant themselves a role
  or edit a role's permissions JSON;
- system roles: Role.is_system marked built-in roles like "Admin", but nothing
  enforced it — they could be deleted or renamed through the API.
"""
import pytest
from rest_framework.test import APIClient

from apps.core.models import User
from apps.rbac.models import Role, RoleAssignment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="rbac@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def system_role():
    return Role.objects.create(name="Admin", name_ar="مدير", is_system=True, permissions={"hr": ["view"]})


@pytest.fixture
def custom_role():
    return Role.objects.create(name="Viewer", name_ar="مشاهد", is_system=False, permissions={})


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


@pytest.mark.django_db
class TestSystemRoleProtection:
    def test_cannot_delete_a_system_role(self, auth_client, system_role):
        response = auth_client.delete(f"/api/rbac/roles/{system_role.pk}/")
        assert response.status_code == 403
        assert Role.objects.filter(pk=system_role.pk).exists()

    def test_can_delete_a_non_system_role(self, auth_client, custom_role):
        response = auth_client.delete(f"/api/rbac/roles/{custom_role.pk}/")
        assert response.status_code == 204
        assert not Role.objects.filter(pk=custom_role.pk).exists()

    def test_cannot_rename_a_system_role(self, auth_client, system_role):
        response = auth_client.patch(f"/api/rbac/roles/{system_role.pk}/", {"name": "SuperAdmin"})
        assert response.status_code == 403
        system_role.refresh_from_db()
        assert system_role.name == "Admin"

    def test_cannot_unset_is_system(self, auth_client, system_role):
        response = auth_client.patch(f"/api/rbac/roles/{system_role.pk}/", {"is_system": False})
        assert response.status_code == 403

    def test_can_still_tune_permissions_on_a_system_role(self, auth_client, system_role):
        response = auth_client.patch(
            f"/api/rbac/roles/{system_role.pk}/", {"permissions": {"hr": ["view", "edit"]}}, format="json"
        )
        assert response.status_code == 200
        system_role.refresh_from_db()
        assert system_role.permissions == {"hr": ["view", "edit"]}
