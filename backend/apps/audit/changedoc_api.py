from rest_framework import serializers, viewsets

from apps.tenants.mixins import TenantScopedMixin

from .models import ChangeDocument, ChangeDocumentItem


class ChangeDocumentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeDocumentItem
        fields = ["id", "field_name", "old_value", "new_value"]


class ChangeDocumentSerializer(serializers.ModelSerializer):
    items = ChangeDocumentItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChangeDocument
        fields = ["id", "content_type", "object_id", "object_repr", "operation",
                  "user", "user_email", "reason", "ip_address", "timestamp", "items"]


class ChangeDocumentViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only audit trail. Change documents are written by the recorder, never
    edited — an audit log you can alter isn't an audit log."""

    queryset = ChangeDocument.objects.prefetch_related("items").select_related("user")
    serializer_class = ChangeDocumentSerializer
    filterset_fields = ["content_type", "object_id", "operation", "user"]
