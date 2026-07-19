from rest_framework import serializers
from .models import Role, UserRole, FieldPermission, RecordPermission, PermissionAudit

class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(source='users.count', read_only=True)
    permission_names = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = '__all__'

    def get_permission_names(self, obj):
        return [p.codename for p in obj.django_permissions.all()]

class UserRoleSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = UserRole
        fields = '__all__'

class FieldPermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    model_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = FieldPermission
        fields = '__all__'

class RecordPermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    model_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = RecordPermission
        fields = '__all__'

class PermissionAuditSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PermissionAudit
        fields = '__all__'
