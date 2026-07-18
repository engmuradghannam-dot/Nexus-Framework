from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.consistency import CompanyConsistencyMixin

from apps.core.nested import NestedLineItemsMixin

from apps.core.workflow import run_side_effect, validate_transition

from .models import (
    GoodsReceipt,
    LatePenaltyTerm,
    SupplierScore,
    SupplierScorecard,
    SupplierScorecardCriterion,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchasePayment,
    PurchaseTaxCharge,
    Supplier,
)

PO_TRANSITIONS = {
    "Draft": {"Submitted", "Cancelled"},
    "Submitted": {"Received", "Cancelled"},
    "Received": set(),
    "Cancelled": set(),
}


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class PurchaseOrderItemSerializer(CompanyConsistencyMixin, serializers.ModelSerializer):
    owner_field = "purchase_order"
    item_name = serializers.CharField(source="item.item_name", read_only=True)
    item_code = serializers.CharField(source="item.item_code", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = "__all__"
        extra_kwargs = {"purchase_order": {"required": False}}


class PurchaseTaxChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseTaxCharge
        fields = "__all__"


class PurchasePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasePayment
        fields = "__all__"


class PurchaseOrderSerializer(CompanyConsistencyMixin, NestedLineItemsMixin, serializers.ModelSerializer):
    total_tax = serializers.ReadOnlyField()
    total_paid = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()
    items = PurchaseOrderItemSerializer(many=True, required=False)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    lines_field = "items"
    lines_model = PurchaseOrderItem
    lines_parent = "purchase_order"
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True, default="")

    class Meta:
        model = PurchaseOrder
        fields = "__all__"

    def validate(self, data):
        data = super().validate(data)
        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(PO_TRANSITIONS, self.instance.status, new_status)
            if new_status == "Submitted":
                # PRC-CTRL-005 / FIN-CTRL-002 are preventive: a PO must not
                # leave Draft without the right authority signing it off.
                approver = data.get("approved_by", self.instance.approved_by)
                probe = self.instance
                probe.approved_by = approver
                for check in (probe.check_approval, probe.check_budget):
                    try:
                        check()
                    except DjangoValidationError as exc:
                        raise serializers.ValidationError(exc.messages[0])
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == "Received":
            run_side_effect(instance.receive_stock)
        return instance


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    qty_accepted = serializers.ReadOnlyField()
    item_code = serializers.CharField(source="po_item.item.item_code", read_only=True)

    class Meta:
        model = GoodsReceiptItem
        fields = "__all__"


class GoodsReceiptSerializer(CompanyConsistencyMixin, serializers.ModelSerializer):
    items = GoodsReceiptItemSerializer(many=True, read_only=True)
    po_number = serializers.CharField(source="purchase_order.po_number", read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = "__all__"
        read_only_fields = ["status", "created_at"]


class PurchaseRequisitionItemSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    preferred_supplier = serializers.CharField(source="item.supplier.name", read_only=True)

    class Meta:
        model = PurchaseRequisitionItem
        fields = "__all__"


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    items = PurchaseRequisitionItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = "__all__"


class SupplierScorecardCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierScorecardCriterion
        fields = "__all__"


class SupplierScoreSerializer(serializers.ModelSerializer):
    criterion_name = serializers.CharField(source="criterion.name", read_only=True)

    class Meta:
        model = SupplierScore
        fields = "__all__"


class SupplierScorecardSerializer(serializers.ModelSerializer):
    scores = SupplierScoreSerializer(many=True, read_only=True)
    weighted_score = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = SupplierScorecard
        fields = "__all__"


class LatePenaltyTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatePenaltyTerm
        fields = "__all__"
