from rest_framework import serializers
from .models import Workflow, WorkflowState, WorkflowTransition

class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = '__all__'

class WorkflowTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTransition
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    states = WorkflowStateSerializer(many=True, read_only=True)
    transitions = WorkflowTransitionSerializer(many=True, read_only=True)
    class Meta:
        model = Workflow
        fields = '__all__'
