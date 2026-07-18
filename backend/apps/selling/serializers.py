from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.nested import NestedLineItemsMixin

from apps.core.workflow import run_side_effect, validate_transition

from .models import CommissionRule, CustomerTier, StockReservation  # noqa: F401
from .models import Customer, SalesOrder, SalesOrderItem, SalesPayment, SalesTaxCharge

SO_TRANSITIONS = {
    "Draft": {"Submitted", "Cancelled"},
    "Submitted": {"Delivered", "Cancelled"},
    "Delivered": set(),
    "Cancelled": set(),
}


class _DuplicatePartyMixin:
    """CRM-CTRL-002: flag potential duplicates by email/phone within a company.

    Email/phone are not unique columns (blank is common and legitimate), so
    this checks only values that are actually supplied.
    """

    def _check_duplicates(self, data, model):
        company = data.get("company", getattr(self.instance, "company", None))
        if company is None:
            return
        for field in ("email", "phone", "mobile"):
            value = data.get(field, getattr(self.instance, field, "") if self.instance else "")
            if not value:
                continue
            clash = model.objects.filter(company=company, **{f"{field}__iexact": value})
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            existing = clash.first()
            if existing:
                raise serializers.ValidationError({
                    field: f"عميل موجود بنفس البيانات / Possible duplicate: "
                           f"'{existing.name}' already uses this {field}."
                })


class CustomerSerializer(_DuplicatePartyMixin, serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

    def validate(self, data):
        self._check_duplicates(data, Customer)
        return data


class SalesOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.item_name", read_only=True)
    item_code = serializers.CharField(source="item.item_code", read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = "__all__"
        extra_kwargs = {"sales_order": {"required": False}}


class SalesTaxChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTaxCharge
        fields = "__all__"


class SalesPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPayment
        fields = "__all__"


class SalesOrderSerializer(NestedLineItemsMixin, serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, required=False)
    total_tax = serializers.ReadOnlyField()
    total_paid = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    lines_field = "items"
    lines_model = SalesOrderItem
    lines_parent = "sales_order"
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True, default="")

    class Meta:
        model = SalesOrder
        fields = "__all__"

    def validate(self, data):
        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(SO_TRANSITIONS, self.instance.status, new_status)
            if new_status == "Submitted":
                # SAL-CTRL-001 (credit) and SAL-CTRL-004 (discount) are
                # preventive controls: they must block the Draft -> Submitted
                # confirmation, not merely warn after the fact.
                for check in (
                    self.instance.check_credit_limit,
                    self.instance.check_discount_authorization,
                ):
                    try:
                        check()
                    except DjangoValidationError as exc:
                        raise serializers.ValidationError(exc.messages[0])
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == "Submitted":
            # SAL-RULE-002 / SAL-RULE-004: confirmation commits the stock that
            # exists and backorders whatever doesn't.
            run_side_effect(instance.reserve_stock)
        if old_status != new_status and new_status == "Delivered":
            run_side_effect(instance.deliver_stock)
        return instance


class StockReservationSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = StockReservation
        fields = "__all__"


class CustomerTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTier
        fields = "__all__"


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = "__all__"
