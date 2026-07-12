from rest_framework import serializers

from .models import Role, RoleAssignment


class RoleSerializer(serializers.ModelSerializer):
    assigned_count = serializers.IntegerField(source="assignments.count", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "name_ar", "description", "permissions", "is_system", "assigned_count"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name_ar", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = ["id", "user", "role", "role_name", "user_email", "assigned_at"]
