from rest_framework import serializers

from .models import ModuleRecord


class ModuleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleRecord
        fields = ["id", "module", "data", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
