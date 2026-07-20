from rest_framework import serializers
from .models import (
    WorkCenter, BOM, BOMItem, Routing, RoutingOperation,
    ManufacturingOrder, ManufacturingOrderOperation,
    MaterialRequisition, MaterialRequisitionItem
)


class WorkCenterSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    operation_count = serializers.IntegerField(source='operations.count', read_only=True)

    class Meta:
        model = WorkCenter
        fields = '__all__'


class BOMItemSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)
    component_sku = serializers.CharField(source='component.sku', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    effective_quantity = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)

    class Meta:
        model = BOMItem
        fields = '__all__'


class BOMSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    items = BOMItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = BOM
        fields = '__all__'


class RoutingOperationSerializer(serializers.ModelSerializer):
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    work_center_code = serializers.CharField(source='work_center.code', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = RoutingOperation
        fields = '__all__'


class RoutingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    operations = RoutingOperationSerializer(many=True, read_only=True)
    operation_count = serializers.IntegerField(source='operations.count', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Routing
        fields = '__all__'


class ManufacturingOrderOperationSerializer(serializers.ModelSerializer):
    routing_operation_name = serializers.CharField(source='routing_operation.name', read_only=True)
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    work_center_code = serializers.CharField(source='work_center.code', read_only=True)
    completed_by_name = serializers.CharField(source='completed_by.username', read_only=True)
    total_time = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ManufacturingOrderOperation
        fields = '__all__'


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    bom_version = serializers.CharField(source='bom.version', read_only=True)
    routing_version = serializers.CharField(source='routing.version', read_only=True)
    operations = ManufacturingOrderOperationSerializer(many=True, read_only=True)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    remaining_quantity = serializers.IntegerField(read_only=True)
    yield_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    requisition_count = serializers.IntegerField(source='requisitions.count', read_only=True)

    class Meta:
        model = ManufacturingOrder
        fields = '__all__'
        read_only_fields = ['order_number']

    def validate(self, attrs):
        planned_start = attrs.get('planned_start', getattr(self.instance, 'planned_start', None))
        planned_end = attrs.get('planned_end', getattr(self.instance, 'planned_end', None))
        if planned_start and planned_end and planned_end < planned_start:
            raise serializers.ValidationError('Planned end must be on or after planned start')
        return attrs


class MaterialRequisitionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    fulfillment_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = MaterialRequisitionItem
        fields = '__all__'


class MaterialRequisitionSerializer(serializers.ModelSerializer):
    manufacturing_order_number = serializers.CharField(source='manufacturing_order.order_number', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    items = MaterialRequisitionItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(source='items.count', read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MaterialRequisition
        fields = '__all__'
        read_only_fields = ['requisition_number']
