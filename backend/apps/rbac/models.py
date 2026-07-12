"""Role-based access control: roles carry per-module permissions."""
from django.conf import settings
from django.db import models

ACTIONS = ["view", "create", "edit", "delete"]


class Role(models.Model):
    name = models.CharField(max_length=80, unique=True)
    name_ar = models.CharField(max_length=80, blank=True)
    description = models.CharField(max_length=255, blank=True)
    # {"crm": ["view","create"], "accounting": ["view"], ...}
    permissions = models.JSONField(default=dict, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rbac_roles"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def can(self, module, action):
        return action in (self.permissions.get(module) or [])


class RoleAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rbac_role_assignments"
        unique_together = ["user", "role"]

    def __str__(self):
        return f"{self.user} -> {self.role}"


def user_can(user, module, action):
    """True if the user may perform action on module. Superusers always can."""
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    for a in RoleAssignment.objects.filter(user=user).select_related("role"):
        if a.role.can(module, action):
            return True
    return False
