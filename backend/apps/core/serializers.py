from rest_framework import serializers
from .models import User, Branch, Warehouse


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'department', 'job_title', 'permissions_level',
                  'is_department_head', 'avatar', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class BranchSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    warehouse_count = serializers.IntegerField(source='warehouses.count', read_only=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'address', 'latitude', 'longitude',
                  'phone', 'manager', 'manager_name', 'warehouse_count',
                  'is_active', 'created_at']


class WarehouseSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    parent_name = serializers.CharField(source='parent_warehouse.name', read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)
    sub_warehouse_count = serializers.IntegerField(source='sub_warehouses.count', read_only=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'branch', 'branch_name', 'parent_warehouse',
                  'parent_name', 'capacity', 'current_occupancy', 'occupancy_rate',
                  'sub_warehouse_count', 'is_active', 'created_at']
