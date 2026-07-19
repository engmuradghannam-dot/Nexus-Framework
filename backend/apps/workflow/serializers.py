from rest_framework import serializers

from apps.core.nested import NestedLineItemsMixin

from .models import (
    State, Transition, Workflow, WorkflowHistory, WorkflowInstance,
)


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "workflow", "key", "label", "label_ar", "is_initial", "is_final"]
        extra_kwargs = {"workflow": {"required": False}}
        validators = []


class TransitionSerializer(serializers.ModelSerializer):
    from_key = serializers.CharField(source="from_state.key", read_only=True)
    to_key = serializers.CharField(source="to_state.key", read_only=True)
    role_name = serializers.CharField(source="required_role.name", read_only=True, default=None)

    class Meta:
        model = Transition
        fields = ["id", "workflow", "name", "from_state", "to_state",
                  "from_key", "to_key", "required_role", "role_name"]


class WorkflowSerializer(NestedLineItemsMixin, serializers.ModelSerializer):
    states = StateSerializer(many=True, required=False)

    lines_field = "states"
    lines_model = State
    lines_parent = "workflow"

    class Meta:
        model = Workflow
        fields = ["id", "tenant", "name", "document_type", "is_active",
                  "states", "created_at"]
        read_only_fields = ["created_at"]


class WorkflowHistorySerializer(serializers.ModelSerializer):
    from_key = serializers.CharField(source="from_state.key", read_only=True, default=None)
    to_key = serializers.CharField(source="to_state.key", read_only=True, default=None)
    actor_email = serializers.CharField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = WorkflowHistory
        fields = ["id", "from_key", "to_key", "actor_email", "note", "timestamp"]


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    state_key = serializers.CharField(source="current_state.key", read_only=True)
    state_label = serializers.CharField(source="current_state.label", read_only=True)
    workflow_name = serializers.CharField(source="workflow.name", read_only=True)
    history = WorkflowHistorySerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowInstance
        fields = ["id", "workflow", "workflow_name", "current_state", "state_key",
                  "state_label", "object_id", "history", "created_at", "updated_at"]
