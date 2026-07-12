from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "subdomain", "plan", "is_active", "created_at", "user_count"]

    def get_user_count(self, obj):
        return obj.users.count() if hasattr(obj, "users") else 0
