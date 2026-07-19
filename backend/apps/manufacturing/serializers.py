from rest_framework import serializers

from apps.core.consistency import CompanyConsistencyMixin

from apps.core.workflow import run_side_effect, validate_transition

from .models import BOM, BOMItem, JobCard, QualityInspection, QualityInspectionParameter, WorkOrder, ProductionBatch, BatchConsumption, ScheduleSlot, Workstation

WO_TRANSITIONS = {
    "Draft": {"In Progress", "Cancelled"},
    "In Progress": {"Completed", "Cancelled"},
    "Completed": set(),
    "Cancelled": set(),
}


class BOMItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMItem
        fields = "__all__"


class BOMSerializer(CompanyConsistencyMixin, serializers.ModelSerializer):
    items = BOMItemSerializer(many=True, read_only=True)
    raw_materials_cost = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = BOM
        fields = "__all__"


class WorkOrderSerializer(CompanyConsistencyMixin, serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = "__all__"

    def validate(self, data):
        data = super().validate(data)
        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(WO_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == "Completed":
            run_side_effect(instance.complete_production)
            instance.refresh_from_db()
        return instance


class JobCardSerializer(serializers.ModelSerializer):
    time_in_mins = serializers.ReadOnlyField()
    employee_name = serializers.SerializerMethodField()
    work_order_number = serializers.CharField(source="work_order.wo_number", read_only=True)

    class Meta:
        model = JobCard
        fields = "__all__"
        read_only_fields = ["actual_operating_cost", "started_time", "ended_time", "status"]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip() if obj.employee else ""


class QualityInspectionParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityInspectionParameter
        fields = "__all__"
        read_only_fields = ["status"]


class QualityInspectionSerializer(serializers.ModelSerializer):
    parameters = QualityInspectionParameterSerializer(many=True, read_only=True)
    item_name = serializers.CharField(source="item.item_name", read_only=True)

    class Meta:
        model = QualityInspection
        fields = "__all__"
        read_only_fields = ["status"]


class BatchConsumptionSerializer(serializers.ModelSerializer):
    input_item_code = serializers.CharField(source="input_item.item_code", read_only=True)

    class Meta:
        model = BatchConsumption
        fields = ["id", "input_item", "input_item_code", "input_batch_no",
                  "nominal_qty", "actual_qty", "batch_potency"]


class ProductionBatchSerializer(serializers.ModelSerializer):
    consumptions = BatchConsumptionSerializer(many=True, read_only=True)
    output_item_code = serializers.CharField(source="output_item.item_code", read_only=True)
    wo_number = serializers.CharField(source="work_order.wo_number", read_only=True)

    class Meta:
        model = ProductionBatch
        fields = ["id", "company", "work_order", "wo_number", "output_item",
                  "output_item_code", "output_batch_no", "output_qty",
                  "output_potency", "manufactured_on", "consumptions"]
        read_only_fields = ["manufactured_on"]


class ScheduleSlotSerializer(serializers.ModelSerializer):
    workstation_code = serializers.CharField(source="workstation.code", read_only=True)
    wo_number = serializers.CharField(source="work_order.wo_number", read_only=True)

    class Meta:
        model = ScheduleSlot
        fields = ["id", "company", "workstation", "workstation_code", "work_order",
                  "wo_number", "start", "end", "status", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        # Surface the model's overlap check as a clean DRF error.
        from django.core.exceptions import ValidationError as DjangoValidationError
        instance = ScheduleSlot(**{k: v for k, v in attrs.items()})
        if self.instance:
            instance.pk = self.instance.pk
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return attrs
