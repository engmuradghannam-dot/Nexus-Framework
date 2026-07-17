from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.workflow import run_side_effect, validate_transition

from .models import (
    Item,
    ItemBatch,
    ItemGroup,
    ItemSerialNumber,
    StockEntry,
    StockReconciliation,
    StockReconciliationItem,
)

SR_TRANSITIONS = {
    "Draft": {"Submitted", "Cancelled"},
    "Submitted": set(),
    "Cancelled": set(),
}


class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGroup
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    stock_quantity = serializers.ReadOnlyField()
    item_group_name = serializers.CharField(source="item_group.name", read_only=True, default="")

    class Meta:
        model = Item
        fields = "__all__"


class StockEntrySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.item_name", read_only=True)
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True, default="")

    class Meta:
        model = StockEntry
        fields = "__all__"

    def validate(self, data):
        entry_type = data.get("entry_type", getattr(self.instance, "entry_type", None))
        item = data.get("item", getattr(self.instance, "item", None))
        quantity = data.get("quantity", getattr(self.instance, "quantity", None))
        warehouse = data.get("warehouse", getattr(self.instance, "warehouse", None))
        bin_location = data.get("bin_location", getattr(self.instance, "bin_location", None))
        if warehouse and warehouse.uses_bins and bin_location is None:
            # WHS-CTRL-001: once a warehouse is binned, stock must land somewhere
            # findable. Warehouses with no bins defined are unaffected.
            raise serializers.ValidationError(
                {"bin_location": f"{warehouse.name} uses bin locations; a bin is required."}
            )
        if bin_location and warehouse and bin_location.warehouse_id != warehouse.pk:
            raise serializers.ValidationError(
                {"bin_location": "Bin does not belong to the selected warehouse."}
            )
        if entry_type == "Receipt" and bin_location and quantity:
            if not bin_location.can_hold(quantity):
                raise serializers.ValidationError(
                    {"bin_location": f"Bin {bin_location.code} cannot hold {quantity} units "
                                     f"(free {bin_location.free_capacity})."}
                )
        if entry_type == "Receipt" and warehouse and quantity:
            # WHS-RULE-004: check the destination can hold it before accepting.
            incoming = quantity
            if self.instance and self.instance.entry_type == "Receipt":
                incoming -= self.instance.quantity
            try:
                warehouse.check_capacity(incoming)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages[0])
        if entry_type == "Issue" and item and quantity:
            available = (
                item.stock_in_warehouse(warehouse) if warehouse else item.stock_quantity
            )
            if self.instance and self.instance.entry_type == "Issue":
                # editing an existing Issue: the quantity it already consumed
                # is still "available" from the item's point of view
                available += self.instance.quantity
            if available < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {item.item_code}: available {available}, requested {quantity}."
                )
        return data


class ItemSerialNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSerialNumber
        fields = "__all__"


class ItemBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBatch
        fields = "__all__"


class StockReconciliationItemSerializer(serializers.ModelSerializer):
    difference = serializers.ReadOnlyField()
    total_difference_value = serializers.ReadOnlyField()

    class Meta:
        model = StockReconciliationItem
        fields = "__all__"


class StockReconciliationSerializer(serializers.ModelSerializer):
    total_difference_value = serializers.ReadOnlyField()

    class Meta:
        model = StockReconciliation
        fields = "__all__"

    def validate(self, data):
        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(SR_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == "Submitted":
            run_side_effect(instance.apply_adjustments)
        return instance
