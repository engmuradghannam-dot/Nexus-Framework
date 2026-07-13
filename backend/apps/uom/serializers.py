from rest_framework import serializers

from .models import ItemVariant, UnitOfMeasure, UOMConversion


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = "__all__"
        read_only_fields = ["tenant"]


class UOMConversionSerializer(serializers.ModelSerializer):
    from_code = serializers.CharField(source="from_unit.code", read_only=True)
    to_code = serializers.CharField(source="to_unit.code", read_only=True)

    class Meta:
        model = UOMConversion
        fields = ["id", "from_unit", "to_unit", "from_code", "to_code", "factor"]
        read_only_fields = ["tenant"]


class ItemVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemVariant
        fields = "__all__"
        read_only_fields = ["tenant"]
