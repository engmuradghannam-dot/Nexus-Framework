from rest_framework import serializers

from .models import PurchaseDoc


class PurchaseDocSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseDoc
        fields = "__all__"
        read_only_fields = ["status", "linked_ref", "created_at", "tenant"]
