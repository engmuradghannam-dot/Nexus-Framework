from rest_framework import serializers

from .models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "name", "name_ar", "symbol", "is_base", "is_active", "rate_to_base", "updated_at"]
