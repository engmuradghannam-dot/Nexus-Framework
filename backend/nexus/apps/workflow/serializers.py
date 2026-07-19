from rest_framework import serializers
from .models import Workflow, WorkflowStep, ApprovalRequest, ApprovalAction

class WorkflowStepSerializer(serializers.ModelSerializer):
    approver_names = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowStep
        fields = '__all__'

    def get_approver_names(self, obj):
        return [u.username for u in obj.approvers.all()]

class WorkflowSerializer(serializers.ModelSerializer):
    steps = WorkflowStepSerializer(many=True, read_only=True)
    step_count = serializers.IntegerField(source='steps.count', read_only=True)

    class Meta:
        model = Workflow
        fields = '__all__'

class ApprovalActionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    step_name = serializers.CharField(source='step.name', read_only=True)

    class Meta:
        model = ApprovalAction
        fields = '__all__'

class ApprovalRequestSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    current_step_name = serializers.CharField(source='current_step.name', read_only=True)
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)
    action_count = serializers.IntegerField(source='actions.count', read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = '__all__'
