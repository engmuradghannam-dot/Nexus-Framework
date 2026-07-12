from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "user_email", "action", "module", "object_ref", "changes", "ip_address", "timestamp"]
