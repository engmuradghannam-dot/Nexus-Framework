from rest_framework import serializers

from apps.core.nested import NestedLineItemsMixin

from .models import ApprovalRequest, ApprovalStep, ReleaseLevel, ReleaseStrategy


class ReleaseLevelSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = ReleaseLevel
        fields = ["id", "strategy", "sequence", "role", "role_name", "label"]
        extra_kwargs = {"strategy": {"required": False}}
        # (strategy, sequence) unique_together generates a validator that
        # requires the parent present, which breaks nested creation; the DB
        # constraint still enforces uniqueness.
        validators = []


class ReleaseStrategySerializer(NestedLineItemsMixin, serializers.ModelSerializer):
    levels = ReleaseLevelSerializer(many=True, required=False)

    lines_field = "levels"
    lines_model = ReleaseLevel
    lines_parent = "strategy"

    class Meta:
        model = ReleaseStrategy
        fields = ["id", "tenant", "name", "document_type", "min_amount",
                  "is_active", "levels", "created_at"]
        read_only_fields = ["created_at"]


class ApprovalStepSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="level.role.name", read_only=True)
    sequence = serializers.IntegerField(source="level.sequence", read_only=True)
    acted_by_email = serializers.CharField(source="acted_by.email", read_only=True, default=None)

    class Meta:
        model = ApprovalStep
        fields = ["id", "sequence", "role_name", "decision", "acted_by",
                  "acted_by_email", "comment", "acted_at"]


class ApprovalRequestSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)
    strategy_name = serializers.CharField(source="strategy.name", read_only=True)
    current_sequence = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = ["id", "strategy", "strategy_name", "document_type", "amount",
                  "object_id", "requested_by", "status", "current_sequence",
                  "steps", "created_at"]
        read_only_fields = ["status", "created_at"]

    def get_current_sequence(self, obj):
        step = obj.current_step
        return step.level.sequence if step else None
