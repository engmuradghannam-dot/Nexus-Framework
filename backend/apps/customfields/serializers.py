from rest_framework import serializers

from .models import CustomField


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = ["id", "module", "field_key", "label", "label_ar", "field_type",
                  "options", "required", "order", "is_active"]
