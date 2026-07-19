from rest_framework import serializers, viewsets

from apps.core.nested import NestedLineItemsMixin
from apps.tenants.mixins import TenantScopedMixin

from .models import AutomatedAction, AutomatedActionStep


class AutomatedActionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomatedActionStep
        fields = ["id", "action", "order", "step_type", "target_field",
                  "target_value", "message", "webhook", "is_active"]
        extra_kwargs = {"action": {"required": False}}
        validators = []


class AutomatedActionSerializer(NestedLineItemsMixin, serializers.ModelSerializer):
    steps = AutomatedActionStepSerializer(many=True, required=False)

    lines_field = "steps"
    lines_model = AutomatedActionStep
    lines_parent = "action"

    class Meta:
        model = AutomatedAction
        fields = ["id", "tenant", "name", "model_label", "trigger",
                  "condition_field", "condition_operator", "condition_value",
                  "is_active", "run_count", "steps", "created_at"]
        read_only_fields = ["run_count", "created_at"]


class AutomatedActionViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    """Define no-code rules: on an event, if a condition holds, do something."""

    queryset = AutomatedAction.objects.prefetch_related("steps")
    serializer_class = AutomatedActionSerializer
    filterset_fields = ["model_label", "trigger", "is_active"]
    pagination_class = None
