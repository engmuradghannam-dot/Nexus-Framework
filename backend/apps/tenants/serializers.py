from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    # Whether this tenant is on its own physical database or the shared default.
    isolation = serializers.SerializerMethodField()
    db_alias = serializers.ReadOnlyField()
    # We accept database_url on write, but never echo the full DSN back — it
    # carries credentials. The UI shows isolation status, not the secret.
    database_url = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_dedicated_db = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "subdomain", "plan", "is_active",
                  "created_at", "user_count", "isolation", "db_alias",
                  "database_url", "has_dedicated_db"]

    def get_user_count(self, obj):
        return obj.users.count() if hasattr(obj, "users") else 0

    def get_has_dedicated_db(self, obj):
        return bool(obj.database_url)

    def get_isolation(self, obj):
        return "dedicated" if obj.database_url else "shared"
