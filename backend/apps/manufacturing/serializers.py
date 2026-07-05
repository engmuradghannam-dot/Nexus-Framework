from rest_framework import serializers
from .models import BOM, BOMItem, WorkOrder

class BOMItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMItem
        fields = '__all__'

class BOMSerializer(serializers.ModelSerializer):
    items = BOMItemSerializer(many=True, read_only=True)
    raw_materials_cost = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()
    class Meta:
        model = BOM
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'
